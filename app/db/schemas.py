# -*- coding: utf-8 -*-
from pydantic import BaseModel
from typing import Optional

# --- Схема для інформації про харчування ---
class NutritionInfo(BaseModel):
    food_item: str
    calories: float
    protein: float
    fat: float
    carbohydrates: float

# --- Схеми для користувача ---
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
        from_attributes = True # orm_mode = True for pydantic v1