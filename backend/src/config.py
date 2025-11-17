import os
from pydantic_settings import BaseSettings
from loguru import logger

class Settings(BaseSettings):
    API_PREFIX: str  = os.getenv("API_PREFIX", "/meditron-api")

config = Settings()
logger.info(config)