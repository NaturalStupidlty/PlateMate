# -*- coding: utf-8 -*-
import google.generativeai as genai
from app.core.config import settings
from app.db.schemas import NutritionInfo
from PIL import Image
import io
import json
from typing import Optional
import traceback 

# Gemini API config
genai.configure(api_key = settings.GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')

# PROMPT
JSON_PROMPT = """
Act as a professional nutritionist. Analyze the food items in the image.
Based on your analysis, provide a detailed breakdown of each food item, including its name, estimated weight in grams, calories, protein, fat, and carbohydrates.
Finally, provide the total nutritional values for the entire meal. In the 'total' object, set the 'food_item' field to a descriptive summary of the entire meal (e.g., 'Grilled chicken with broccoli' or 'Scrambled eggs with toast').
Respond ONLY with a valid JSON object in the following format, without any additional text or explanations.

{
  "items": [
    {
      "food_item": "...",
      "weight_grams": ...,
      "calories": ...,
      "protein": ...,
      "fat": ...,
      "carbohydrates": ...
    }
  ],
  "total": {
    "food_item": "Descriptive name of the meal",
    "calories": ...,
    "protein": ...,
    "fat": ...,
    "carbohydrates": ...
  }
}
"""

async def get_nutrition_from_image(image_bytes: bytes) -> Optional[NutritionInfo]:
    """
    Sends the image to the Gemini API and returns the total nutritional value.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        
        response = model.generate_content([JSON_PROMPT, image])
        
        # --- DEBUG---
        print("\n--- Gemini API Raw Response ---")
        print(response.text)
        print("-----------------------------\n")
        
        
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
        
        
        nutrition_data = json.loads(cleaned_response_text)
        
        # Converting common data into our Pydantic schema
        total_nutrition = nutrition_data.get("total")
        if total_nutrition:
            return NutritionInfo(**total_nutrition)
            
        return None

    except Exception as e:
        # --- DEBUG ---
        print("\n--- Full Exception Details ---")
        traceback.print_exc()
        print("----------------------------\n")
        return None