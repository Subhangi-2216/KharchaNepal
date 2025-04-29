from pydantic_settings import BaseSettings, SettingsConfigDict
import os

# Determine the base directory (backend/)
# __file__ points to config.py
# os.path.dirname(__file__) gives the directory containing config.py (backend/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE_PATH = os.path.join(BASE_DIR, '.env')

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH)

settings = Settings() 