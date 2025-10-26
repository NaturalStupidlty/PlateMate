"""
PyTorch pipeline:
- one-hot → projection
- cross-attention between feature-projection (query) and ada_embedding (kv)
- final embedding trained with batch-hard triplet loss
- train loop + save model
"""

import os
import pandas as pd
import random
from tqdm import tqdm
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# ----------------------------
# CONFIG
# ----------------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 32                # batch size (for embedding-based triplet loss)
IMG_SIZE = 224                 # image resize for encoder
EMBED_DIM = 512                # dimension of ada/clip embeddings (will align)
FEAT_DIM = 12                  # dimension of hot vectors
CAT_EMBED_DIM = 512            # dimension for projected category embedding
NUM_HEADS = 8                  # heads in cross-attention (must divide embed dim)
MARGIN = 0.3                   # triplet margin
NUM_EPOCHS = 100
LEARNING_RATE = 1e-4
MODEL_SAVE_PATH = "crossatt_triplet.pth"

class FoodDataset(Dataset):
    def __init__(self, pkl_file: str, transform=None):
        self.pkl_file = pkl_file
        self.transform = transform
        self.samples = (pd.read_pickle(pkl_file)).to_dict(orient='records')
        # build label -> indices mapping for sampling positives/negatives
        self.labels = set([row["cluster"] for row in self.samples])
        self.label2indices = {i : [] for i in self.labels}
        for idx, s in enumerate(self.samples):
            self.label2indices[s["cluster"]].append(idx)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]

# Triplet sampling wrapper
class TripletFoodDataset(Dataset):
    """
    Returns triplets (anchor_img, positive_img, negative_img, anchor_label)
    sampled on-the-fly from FoodJSONLDataset.
    """
    def __init__(self, base_dataset: FoodDataset):
        self.base = base_dataset
        self.labels = list(self.base.labels)
        self.label2indices = self.base.label2indices

    def __len__(self):
        return len(self.base)

    def __getitem__(self, idx):
        anchor_img, anchor_label = self.base[idx]["embedding"], self.base[idx]["cluster"]
        # sample positive:
        pos_list = self.label2indices[self.base.samples[idx]["cluster"]]
        pos_idx = idx
        # ensure positive different from anchor
        if len(pos_list) > 1:
            while pos_idx == idx:
                pos_idx = random.choice(pos_list)
        else:
            pos_idx = idx  # fallback (rare)
        positive_img = self.base[pos_idx]["embedding"]
        # sample negative from different label
        neg_label = anchor_label
        while neg_label == anchor_label:
            neg_label = random.choice(range(len(self.labels)))
        neg_idx = random.choice(self.label2indices[self.labels[neg_label]])
        negative_img = self.base[neg_idx]["embedding"]
        anchor_hot = self.base[pos_idx]["hot_vector"]
        positive_hot = self.base[pos_idx]["hot_vector"]
        negative_hot = self.base[neg_idx]["hot_vector"]
        return anchor_img, positive_img, negative_img, anchor_hot, positive_hot, negative_hot

# ----------------------------
# MODEL: classifier->proj -> cross-attention -> final embedding
# ----------------------------
class CrossAttTripletModel(nn.Module):
    def __init__(self, num_features: int, ada_dim=EMBED_DIM, cat_proj_dim=CAT_EMBED_DIM, n_heads=NUM_HEADS):
        super().__init__()
        self.num_classes = num_features
        self.ada_dim = ada_dim
        self.cat_proj_dim = cat_proj_dim

        # project one-hot (num_classes) -> category embedding vector (cat_proj_dim)
        self.cat_proj = nn.Sequential(
            nn.Linear(num_features, cat_proj_dim),
            nn.GELU(),
            nn.Linear(cat_proj_dim, ada_dim)  # make query dim equal to ada dim for attention
        )

        # If ada_dim != ada_dim then we'd adjust; queries and keys must match embed_dim for MultiheadAttention
        self.attn = nn.MultiheadAttention(embed_dim=ada_dim, num_heads=n_heads, batch_first=True)

        # final projection after attention
        self.final_norm = nn.LayerNorm(ada_dim)
        self.final_mlp = nn.Sequential(
            nn.Linear(ada_dim, ada_dim),
            nn.GELU(),
            nn.Linear(ada_dim, ada_dim)
        )

    def forward(self, ada_embeddings: torch.Tensor, labels_onehot: torch.Tensor):
        """
        ada_embeddings: (B, ada_dim)  - image embeddings (keys/values)
        labels_onehot: (B, num_classes) - ground truth one-hot vectors (during training)
        Returns: final_embeddings (B, ada_dim), classifier_logits (B, num_classes)
        """

        # project categorical hot vector -> cat_proj embedding (B, ada_dim)
        cat_vec = self.cat_proj(labels_onehot)  # (B, ada_dim)

        # prepare for attention: MultiheadAttention with batch_first=True expects (B, S, E)
        # we set sequence length S=1 for both queries and keys/values
        queries = cat_vec.unsqueeze(1)           # (B, 1, ada_dim)
        keys = ada_embeddings.unsqueeze(1)       # (B, 1, ada_dim)
        values = ada_embeddings.unsqueeze(1)     # (B, 1, ada_dim)

        # cross-attention: queries attend to keys/values
        attn_out = self.attn(query=queries, key=keys, value=values)[0]  # (B,1,ada_dim)
        attn_out = attn_out.squeeze(1)  # (B, ada_dim)

        # final MLP + residual + norm
        out = self.final_norm(attn_out + ada_embeddings)  # residual with ada_embeddings
        out = self.final_mlp(out)  # (B, ada_dim)
        out = F.normalize(out, dim=-1)  # normalize embeddings for triplet loss / cosine distance
        return out

# ----------------------------
# Triplet loss: batch-hard mining
# ----------------------------

def batch_hard_triplet_loss(a_emb: torch.Tensor, p_emb: torch.Tensor, n_emb: torch.Tensor, margin: float = MARGIN) -> torch.Tensor:
    pos_dist = (a_emb - p_emb).pow(2).sum(dim=1)
    neg_dist = (a_emb - n_emb).pow(2).sum(dim=1)
    loss_raw = F.relu(pos_dist - neg_dist + margin)
    loss = loss_raw.mean()
    return loss

# ----------------------------
# UTIL: collate for TripletDataLoader
# ----------------------------

def triplet_collate_fn(batch):
    anchors, positives, negatives, a_hotes, p_hotes, n_hotes = [], [], [], [], [], []
    for a, p, n, a_h, p_h, n_h in batch:
        anchors.append(torch.Tensor(a))
        positives.append(torch.Tensor(p))
        negatives.append(torch.Tensor(n))
        a_hotes.append(torch.Tensor(a_h))
        p_hotes.append(torch.Tensor(p_h))
        n_hotes.append(torch.Tensor(n_h))
    anchors = torch.stack(anchors)
    positives = torch.stack(positives)
    negatives = torch.stack(negatives)
    a_hotes = torch.stack(a_hotes)
    p_hotes = torch.stack(p_hotes)
    n_hotes = torch.stack(n_hotes)
    return anchors, positives, negatives, a_hotes, p_hotes, n_hotes

# ----------------------------
# TRAINING LOOP
# ----------------------------
def train(jsonl_path: str, model_save_path=MODEL_SAVE_PATH):
    base_ds = FoodDataset(jsonl_path)  # we will sample triplets via wrapper
    triplet_ds = TripletFoodDataset(base_ds)
    loader = DataLoader(triplet_ds, batch_size=BATCH_SIZE, shuffle=True,
                        collate_fn=triplet_collate_fn, pin_memory=True)

    # instantiate model
    model = CrossAttTripletModel(num_features=FEAT_DIM, ada_dim=EMBED_DIM, cat_proj_dim=CAT_EMBED_DIM, n_heads=NUM_HEADS).to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-5)

    for epoch in range(NUM_EPOCHS):
        model.train()
        total_loss = 0.0
        pbar = tqdm(loader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS}")
        for anchors, positives, negatives, a_hots, p_hots, n_hots in pbar:
            emb_a = model(anchors, a_hots)
            emb_p = model(positives, p_hots)
            emb_n = model(negatives, n_hots)
            loss = batch_hard_triplet_loss(emb_a, emb_p, emb_n, margin=MARGIN)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            pbar.set_postfix({"loss": f"{total_loss / (pbar.n+1):.4f}"})

        avg_loss = total_loss / len(loader)
        print(f"Epoch {epoch+1} avg loss: {avg_loss:.4f}")
    torch.save(model.state_dict(), model_save_path)
    print(f"Saved checkpoint to {model_save_path}")

    df = pd.read_pickle(base_ds.pkl_file)
    df["final_embedding"] = [(model(torch.Tensor(row["embedding"])[None, :], torch.Tensor(row["hot_vector"])[None, :]))[0].detach().numpy() for row in base_ds.samples]
    out_csv = "results_food_features.csv"
    out_pkl = "results_food_features.pkl"
    df.to_csv(out_csv, index=False)
    df.to_pickle(out_pkl)
    print("Training finished.")

pklt = "results_food_features.pkl"
train(pklt, MODEL_SAVE_PATH)
