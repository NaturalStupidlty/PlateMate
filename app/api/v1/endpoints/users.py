# -*- coding: utf-8 -*-
from fastapi import APIRouter
from app.db import schemas

router = APIRouter()

@router.post("/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate):
    """
    Create new user profile
    """
    # TODO: Logic for saving the user to the database
    # Return the data, simulating creation in the database
    return schemas.User(
        id=1,  # Imitation of ID from database
        telegram_id=user.telegram_id,
        weight=user.weight,
        height=user.height,
        age=user.age,
        goal=user.goal
    )