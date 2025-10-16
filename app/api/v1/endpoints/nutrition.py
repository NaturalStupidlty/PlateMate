# -*- coding: utf-8 -*-
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.db import schemas
from app.services import barcode_service, vision_service 

router = APIRouter()

@router.post("/analyze-photo", response_model=schemas.NutritionInfo)
async def analyze_food_by_photo(image: UploadFile = File(...)):
    """
    Takes a photo of food and returns information about its nutritional value.
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    image_bytes = await image.read()
    
    
    nutrition_info = await vision_service.get_nutrition_from_image(image_bytes)
    
    if not nutrition_info:
        raise HTTPException(status_code=500, detail="Could not analyze the image. The model might have failed to return valid data.")
        
    return nutrition_info

@router.post("/analyze-barcode", response_model=schemas.NutritionInfo)
async def analyze_food_by_barcode(image: UploadFile = File(...)):
    """
    Takes a photo of a barcode, recognizes it, and returns product information.
    """
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
    
    
    image_bytes = await image.read()
    barcode = await barcode_service.decode_barcode_from_image(image_bytes)
    
    if not barcode:
        raise HTTPException(status_code=404, detail="Barcode not found on the image.")
        
    # Крок 2: Отримуємо інформацію про продукт за штрихкодом
    product_info = await barcode_service.get_product_info_by_barcode(barcode)
    
    if not product_info:
        raise HTTPException(status_code=404, detail=f"Product with barcode {barcode} not found in the database.")
        
    return product_info