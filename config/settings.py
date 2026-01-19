import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: List[int] = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "633765043,6375918223").split(",")]
    
    # API Configuration
    API_URL: str = os.getenv("API_URL", "http://localhost:8000")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "http://localhost:8000/webapp")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./earnmoney.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    
    # Earning Settings
    MIN_WITHDRAWAL: int = int(os.getenv("MIN_WITHDRAWAL", "100"))
    AD_EARNING: int = int(os.getenv("AD_EARNING", "5"))
    AD_DAILY_LIMIT: int = int(os.getenv("AD_DAILY_LIMIT", "10"))
    AD_COOLDOWN: int = int(os.getenv("AD_COOLDOWN", "60"))
    REFERRAL_BONUS: int = int(os.getenv("REFERRAL_BONUS", "10"))
    
    # Admin Contact Info
    ADMIN_NAME_1: str = os.getenv("ADMIN_NAME_1", "XTﾠMꫝɪᴍﾠ!!")
    ADMIN_TG_1: str = os.getenv("ADMIN_TG_1", "@cr_maim")
    ADMIN_NAME_2: str = os.getenv("ADMIN_NAME_2", "XT Hunter !!")
    ADMIN_TG_2: str = os.getenv("ADMIN_TG_2", "@Huntervai1k")
    ADMIN_WHATSAPP: str = os.getenv("ADMIN_WHATSAPP", "01833515655")
    SUPPORT_GROUP: str = os.getenv("SUPPORT_GROUP", "https://t.me/+OXFzYPTSQXQ3NjVl")
    
    class Config:
        env_file = ".env"

settings = Settings()
