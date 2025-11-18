# -*- coding: utf-8 -*-
from fastapi import APIRouter
from app.api.v1.endpoints import nutrition, users, recommendations, images 

api_router = APIRouter()


api_router.include_router(nutrition.router, prefix="/nutrition", tags=["Nutrition Analysis"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(recommendations.router, prefix="/recommend", tags=["Recommendations"])
api_router.include_router(images.router, prefix="/food", tags=["Food Images"]) 