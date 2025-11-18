# -*- coding: utf-8 -*-
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router
from app.services.recommendation_service import load_recommendation_model 


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API для аналізу харчової цінності за фотографією або штрихкодом.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    print("[INFO] Loading ML models...")
    load_recommendation_model() 
    print("[INFO] ML models loaded.")


app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
async def read_root():
    """
    The main endpoint for testing the API's health.
    """
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}
