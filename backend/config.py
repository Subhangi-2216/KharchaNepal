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

    # Celery settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Gmail API settings
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/api/email/oauth/callback"

    # Encryption key for storing OAuth credentials
    ENCRYPTION_KEY: str = ""

    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH)

settings = Settings() 