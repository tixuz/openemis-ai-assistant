"""Flask Configuration"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Flask configuration"""
    SECRET_KEY = os.getenv("SECRET_KEY", "flask-secret-key-change-in-production")
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
