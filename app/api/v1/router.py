# -*- coding: utf-8 -*-
from fastapi import APIRouter
from app.api.v1.endpoints import nutrition, users

api_router = APIRouter()

# Connecting routers from separate files
api_router.include_router(nutrition.router, prefix="/nutrition", tags=["Nutrition Analysis"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])