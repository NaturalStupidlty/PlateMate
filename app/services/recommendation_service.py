# -*- coding: utf-8 -*-
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import List, Dict, Any, Optional


FEAT_DIM = 12
CAT_EMBED_DIM = 512
EMBED_DIM = 512


CURRENT_FILE = Path(__file__).resolve()
APP_DIR = CURRENT_FILE.parent.parent 
ROOT_DIR = APP_DIR.parent 


POSSIBLE_DIRS = [
    APP_DIR / 'ml_stuff',   
    ROOT_DIR / 'ml_stuff'   
]

ML_DIR = None
for path in POSSIBLE_DIRS:
    if path.exists():
        ML_DIR = path
        print(f"[INFO] Found 'ml_stuff' directory at: {ML_DIR}")
        break


if ML_DIR is None:
    print(f"[WARNING] 'ml_stuff' directory not found in {POSSIBLE_DIRS}")
    ML_DIR = APP_DIR / 'ml_stuff'

MODEL_PATH = ML_DIR / 'crossatt_triplet.pth'
FEATURES_PATH = ML_DIR / 'results_food_features.pkl'
PICTURES_PATH = ML_DIR / 'dish_images.pkl'


class Embedder(nn.Module):
    def __init__(self):
        super().__init__()
        self.cat_proj = nn.Sequential(
            nn.Linear(FEAT_DIM, CAT_EMBED_DIM),
            nn.GELU(),
            nn.Linear(CAT_EMBED_DIM, EMBED_DIM) 
        )

    def forward(self, labels_onehot):
        cat_vec = self.cat_proj(labels_onehot)
        cat_vec = nn.functional.normalize(cat_vec, dim=-1)
        return cat_vec


embedder_model = None
features_df = None
pictures_df = None

def load_recommendation_model():
    global embedder_model, features_df, pictures_df
    
    
    if not ML_DIR.exists():
        print(f"[CRITICAL ERROR] Directory not found: {ML_DIR}")
        return
    
    if not MODEL_PATH.exists():
        print(f"[CRITICAL ERROR] Model file missing: {MODEL_PATH}")
        return

    try:
        embedder_model = Embedder()
        full_dict = torch.load(str(MODEL_PATH), map_location=torch.device('cpu'))
        emb_dict = {
            'cat_proj.0.weight': full_dict['cat_proj.0.weight'],
            'cat_proj.0.bias': full_dict['cat_proj.0.bias'],
            'cat_proj.2.weight': full_dict['cat_proj.2.weight'],
            'cat_proj.2.bias': full_dict['cat_proj.2.bias']
        }
        embedder_model.load_state_dict(emb_dict)
        embedder_model.eval()
        print("[INFO] ✅ Recommendation Embedder loaded.")

        
        features_df = pd.read_pickle(str(FEATURES_PATH))
        print(f"[INFO] ✅ Loaded {len(features_df)} features.")

        
        pictures_df = pd.read_pickle(str(PICTURES_PATH))
        print(f"[INFO] ✅ Loaded {len(pictures_df)} images.")

    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to load ML models: {e}")
        embedder_model = None 

async def get_recommendations(hot_vector: List[int], image_amount: int = 10) -> List[Dict[str, Any]]:
    """Returns a list of IDs and names of dishes."""
    if embedder_model is None or features_df is None:
        raise RuntimeError(f"Recommendation service not initialized. ML_DIR checked: {ML_DIR}")

    
    query_tensor = torch.Tensor(hot_vector).float()
    with torch.no_grad():
        q_emb = embedder_model(query_tensor).detach().cpu().numpy()

    
    all_embeddings = np.stack(features_df['final_embedding'].values)
    similarities = np.dot(all_embeddings, q_emb.T).flatten()
    
    
    top_indices = np.argpartition(similarities, -image_amount)[-image_amount:]
    top_indices = top_indices[np.argsort(similarities[top_indices])][::-1]

    
    results_df = features_df.iloc[top_indices]
    
    final_recommendations = []
    for row in results_df.to_dict('records'):
        final_recommendations.append({
            "id": row.get("index"),
            "food_item": row.get("name", "Unknown Item") 
        })

    return final_recommendations

async def get_image_bytes_by_id(item_id: int) -> Optional[bytes]:
    """
    Gets the bytes of an image by its ID (line number).
    """
    if pictures_df is None:
        raise RuntimeError("Picture database is not initialized.")
    
    try:
        image_row = pictures_df.iloc[item_id]
        image_bytes = image_row['rgb_image']
        return image_bytes
    except IndexError:
        return None
    except Exception as e:
        print(f"Error retrieving image by ID {item_id}: {e}")
        return None