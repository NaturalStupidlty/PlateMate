# -*- coding: utf-8 -*-
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for analyzing nutritional value from a photo or barcode.",
    version="1.0.0"
)


app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
async def read_root():
    """
    The main endpoint for testing API health.
    """
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}


