# -*- coding: utf-8 -*-
from fastapi import APIRouter
from app.db import schemas

router = APIRouter()

@router.post("/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate):
    """
    Create new user profile
    """
    # TODO: Логіка збереження користувача в базу даних
    # Повертаємо дані, імітуючи створення в БД
    return schemas.User(
        id=1,  # Імітація ID з бази даних
        telegram_id=user.telegram_id,
        weight=user.weight,
        height=user.height,
        age=user.age,
        goal=user.goal
    )