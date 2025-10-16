# -*- coding: utf-8 -*-
from fastapi import APIRouter
from app.api.v1.endpoints import nutrition, users

api_router = APIRouter()

# Підключення роутерів з окремих файлів
api_router.include_router(nutrition.router, prefix="/nutrition", tags=["Nutrition Analysis"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])