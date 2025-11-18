# -*- coding: utf-8 -*-
import google.generativeai as genai
from app.core.config import settings
from app.db.schemas import NutritionInfo
from PIL import Image
import io
import json
from typing import Optional
import traceback 


genai.configure(api_key = settings.GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')


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


JSON_PROMPT = f"""
Act as a professional nutritionist. Analyze the food items in the image.

1. Provide a detailed breakdown: name, weight, calories, protein, fat, carbohydrates.
2. Also, classify the ENTIRE meal against the following categories. Return a list of 0s and 1s (1 if true, 0 if false) in the exact order listed below:
{json.dumps(FEATURE_LABELS)}

Respond ONLY with a valid JSON object in the following format:

{{
  "items": [
    {{ "food_item": "...", "weight_grams": ..., "calories": ..., "protein": ..., "fat": ..., "carbohydrates": ... }}
  ],
  "total": {{
    "food_item": "Descriptive name of the meal",
    "calories": ...,
    "protein": ...,
    "fat": ...,
    "carbohydrates": ...,
    "hot_vector": [0, 1, 0, ..., 0] 
  }}
}}
"""

async def get_nutrition_from_image(image_bytes: bytes) -> Optional[NutritionInfo]:

    if not model:
        return None
        
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        response = model.generate_content([JSON_PROMPT, image])
        
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
        nutrition_data = json.loads(cleaned_response_text)
        
        total_nutrition = nutrition_data.get("total")
        if total_nutrition:
            if "hot_vector" not in total_nutrition or len(total_nutrition["hot_vector"]) != 12:
                total_nutrition["hot_vector"] = [0] * 12
            
            return NutritionInfo(**total_nutrition)
            
        return None

    except Exception as e:
        print("\n--- Gemini Error Details ---")
        traceback.print_exc()
        return None