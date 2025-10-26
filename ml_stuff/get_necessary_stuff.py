"""
Get necessary elements for learning:
-raw embeddings
-hot vectors
-labels
"""

import pandas as pd
import torch
from PIL import Image
from io import BytesIO
import numpy as np
from tqdm import tqdm
from transformers import CLIPProcessor, CLIPModel, BlipProcessor, BlipForConditionalGeneration
from sklearn.cluster import KMeans
from matplotlib  import pyplot as plt


pkl_path = "dish_images.pkl"
df = pd.read_pickle(pkl_path)
print(f"[INFO] Loaded {len(df)} rows from {pkl_path}")
print(df.head())


device = "cuda" if torch.cuda.is_available() else "cpu"

clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def to_pil(img_data):
    if isinstance(img_data, Image.Image):
        return img_data
    elif isinstance(img_data, np.ndarray):
        return Image.fromarray(img_data)
    elif isinstance(img_data, bytes):
        return Image.open(BytesIO(img_data)).convert("RGB")
    else:
        raise TypeError(f"Unsupported image format: {type(img_data)}")

embeddings = []

for i, row in tqdm(df.iterrows(), total=len(df), desc="Processing images"):
    pil_img = to_pil(row["rgb_image"])
    clip_inputs = clip_processor(images=pil_img, return_tensors="pt").to(device)
    with torch.no_grad():
        emb = clip_model.get_image_features(**clip_inputs)
    emb = emb.cpu().numpy().flatten()
    embeddings.append(emb)

FEATURE_LABELS = [
    "is a meat product",
    "is fish or seafood",
    "is a dairy product",
    "is a vegetable",
    "is a fruit",
    "is an oil or fat",
    "is a grain (rice/wheat/oats)",
    "is a legume (beans, lentils, soy)",
    "is a spice or herb",
    "is high in sugar",
    "is high in protein",
    "is gluten-free"
]
THRESHOLD = 0.2

def extract_hot_vectors(emb_list, feature_texts):
    proc = CLIPProcessor.from_pretrained(clip_model)
    model = CLIPModel.from_pretrained(clip_model).to(device)

    # prepare text embeddings
    with torch.no_grad():
        text_inputs = proc(text=feature_texts, return_tensors="pt", padding=True).to(device)
        text_emb = model.get_text_features(**text_inputs)   # (K, D)
        text_emb = torch.nn.functional.normalize(text_emb, dim=-1)
        text_emb = (np.asarray(text_emb)).T

    hot_vectors = []
    for i in range(len(emb_list)):
        emb = emb_list[i]
        with torch.no_grad():
            sims = emb @ text_emb / np.linalg.norm(emb)
        hot = (sims >= THRESHOLD).astype(int)
        hot_vectors.append(hot)
    return hot_vectors

hot = extract_hot_vectors(df["embedding"], FEATURE_LABELS)
df["hot_vector"] = hot
embeddings = [embedding.tolist() for embedding in df["embedding"]]
df["embedding"] = embeddings
n_clusters = 32
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
clusters = kmeans.fit_predict(embeddings)
df["cluster"] = clusters

a = 420
b = 69
x = [embedding[a] for embedding in embeddings]
y = [embedding[b] for embedding in embeddings]
fig, ax = plt.subplots()
plt.scatter(x, y, c=clusters)
plt.show()

out_csv = "results_food_features.csv"
out_pkl = "results_food_features.pkl"

df.to_csv(out_csv, index=False)
df.to_pickle(out_pkl)
print(f"[INFO] Saved dataset to {out_csv} and {out_pkl}")
