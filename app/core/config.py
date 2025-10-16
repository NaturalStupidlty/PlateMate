# -*- coding: utf-8 -*-
from ast import Str
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PlateMate"
    API_V1_STR: str = "/api/v1"

    # Секретні ключі
    TELEGRAM_BOT_TOKEN: str
    GOOGLE_API_KEY: str  

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

# harcoding
settings.GOOGLE_API_KEY = "AIzaSyAx_ZbysMYSshwhd6qIlWNBP0f2zvbHbC8"

