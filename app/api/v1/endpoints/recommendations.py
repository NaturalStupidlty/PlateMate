# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Body
from typing import List
from app.db import schemas
from app.services import recommendation_service

router = APIRouter()

@router.post("/", response_model=List[schemas.RecommendedItem]) 
async def get_food_recommendations(query: schemas.RecommendationQuery):
    """
    Takes a "hot vector" of user preferences and returns
    a list of recommended dishes (ID and name).
    """
    try:
        recommendations = await recommendation_service.get_recommendations(query.hot_vector)
        return recommendations
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")