# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from app.services import recommendation_service

router = APIRouter()

@router.get("/image/{item_id}",
    responses = {
        200: {"content": {"image/png": {}}},
        404: {"description": "Image not found"}
    },
    response_class=Response
)
async def get_food_image(item_id: int):
    """
    Gets the ID of the dish and returns its image in PNG format.
    """
    try:
        image_bytes = await recommendation_service.get_image_bytes_by_id(item_id)
        if image_bytes:
            return Response(content=image_bytes, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Image not found for this ID.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")