import torch
import torch.nn as nn
import pandas as pd
from PIL import Image
from io import BytesIO

image_amount = 10
FEAT_DIM = 12  # dimension of hot vectors
CAT_EMBED_DIM = 512  # dimension for projected category embedding


class Embedder(nn.Module):
    def __init__(self):
        super().__init__()
        self.cat_proj = nn.Sequential(
            nn.Linear(FEAT_DIM, CAT_EMBED_DIM),
            nn.GELU(),
            nn.Linear(CAT_EMBED_DIM, CAT_EMBED_DIM)  # make query dim equal to ada dim for attention
        )

    def forward(self, labels_onehot):
        cat_vec = self.cat_proj(labels_onehot)
        cat_vec = nn.functional.normalize(cat_vec, dim=-1)
        return cat_vec


def recommend(query, model_path, emb_pkl_file, pic_pkl_file):
    """
    :param query: user query - hot vector
    :param model_path: path to saved model
    :param emb_pkl_file: pkl file with embeddings
    :param pic_pkl_file: pkl file with pictures
    :return: list of recommendated images
    """
    embedder = Embedder()
    full_dict = torch.load(model_path)
    emb_dict = {'cat_proj.0.weight': full_dict['cat_proj.0.weight'],
                'cat_proj.0.bias': full_dict['cat_proj.0.bias'],
                'cat_proj.2.weight': full_dict['cat_proj.2.weight'],
                'cat_proj.2.bias': full_dict['cat_proj.2.bias']}
    embedder.load_state_dict(emb_dict)
    query = torch.Tensor(query)
    q_emb = embedder(query).detach().numpy()
    samples = (pd.read_pickle(emb_pkl_file)).to_dict(orient='records')
    samples.sort(key=lambda s: s['final_embedding'] @ q_emb, reverse=True)
    indexes = [row['index'] for row in samples[:image_amount]]
    slice = (pd.read_pickle(pic_pkl_file)).iloc[indexes]
    return [Image.open(BytesIO(img)).convert("RGB") for img in slice['rgb_image'].tolist()]
