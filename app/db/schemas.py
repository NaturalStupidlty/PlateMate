# -*- coding: utf-8 -*-
from pydantic import BaseModel
from typing import Optional

# --- Nutrition information scheme ---
class NutritionInfo(BaseModel):
    food_item: str
    calories: float
    protein: float
    fat: float
    carbohydrates: float

# --- User information scheme ---
class UserBase(BaseModel):
    telegram_id: int
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    goal: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int

    class Config:
        from_attributes = True 