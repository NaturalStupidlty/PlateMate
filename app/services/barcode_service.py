# -*- coding: utf-8 -*-
import httpx
from pyzbar.pyzbar import decode
from PIL import Image
import io
from typing import Optional
from app.db.schemas import NutritionInfo
import re 

# API for Open Food Facts
OPENFOODFACTS_API_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

def _parse_quantity(quantity_str: str) -> Optional[float]:
    """
    A helper function to extract a numeric weight/volume value
    from a string (e.g., "500 ml", "1.5 l") and convert it to g/ml.
    """
    if not isinstance(quantity_str, str):
        return None
    
    
    quantity_str = quantity_str.lower().replace(',', '.')
    
    numeric_match = re.search(r'(\d+\.?\d*)', quantity_str)
    if not numeric_match:
        return None
        
    value = float(numeric_match.group(1))
    
    if 'kg' in quantity_str or 'l' in quantity_str:
        value *= 1000
        
    return value

async def decode_barcode_from_image(image_bytes: bytes) -> Optional[str]:
    """
    Recognizes a barcode from a provided image in the form of bytes.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        barcodes = decode(image)
        if barcodes:
            return barcodes[0].data.decode('utf-8')
        return None
    except Exception as e:
        print(f"Error decoding barcode: {e}")
        return None

async def get_product_info_by_barcode(barcode: str) -> Optional[NutritionInfo]:
    """
    Queries the Open Food Facts API and returns nutritional information 
    for the entire product package, if the size is known.
    """
    url = OPENFOODFACTS_API_URL.format(barcode=barcode)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1 and "product" in data:
                    product = data["product"]
                    nutriments = product.get("nutriments", {})
                    
                    if "energy-kcal_100g" in nutriments and "proteins_100g" in nutriments:
                        
                       
                        multiplier = 1.0
                        quantity_str = product.get('quantity')
                        
                        if quantity_str:
                            package_size = _parse_quantity(quantity_str)
                            if package_size and package_size > 0:
                                multiplier = package_size / 100.0
                        
                        # Get base values ​​per 100g, handling possible empty strings
                        calories_100g = float(nutriments.get("energy-kcal_100g") or 0)
                        protein_100g = float(nutriments.get("proteins_100g") or 0)
                        fat_100g = float(nutriments.get("fat_100g") or 0)
                        carbs_100g = float(nutriments.get("carbohydrates_100g") or 0)
                        
                        return NutritionInfo(
                            food_item=product.get("product_name", "Назва невідома"),
                            calories=round(calories_100g * multiplier, 1),
                            protein=round(protein_100g * multiplier, 1),
                            fat=round(fat_100g * multiplier, 1),
                            carbohydrates=round(carbs_100g * multiplier, 1)
                        )
            return None
        except Exception as e:
            print(f"Error fetching data from Open Food Facts: {e}")
            return None

