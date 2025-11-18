# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from typing import Optional, List, Annotated

# --- Схема для інформації про харчування ---
class NutritionInfo(BaseModel):
    food_item: str
    calories: float
    protein: float
    fat: float
    carbohydrates: float
    # ДОДАНО: Вектор ознак страви (12 чисел: 0 або 1)
    # За замовчуванням пустий, якщо це баркод скан
    hot_vector: Optional[List[int]] = None 

# ... (решта файлу без змін: UserBase, UserCreate, User, RecommendationQuery, RecommendedItem) ...
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

class RecommendationQuery(BaseModel):
    hot_vector: Annotated[List[int], Field(min_length=12, max_length=12)]

class RecommendedItem(BaseModel):
    id: int
    food_item: str