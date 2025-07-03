from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Bot settings
    BOT_TOKEN: str
    BOT_USERNAME: str = "ceiling_calc_bot"
    
    # Admin settings
    ADMIN_IDS: List[int] = [5123262366, 545371253, 6733176057]  # Список админов
    
    # Gemini API
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    
    # YooKassa
    YOOKASSA_SHOP_ID: Optional[str] = None
    YOOKASSA_SECRET_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///bot.db"
    
    # Subscription prices (в рублях)
    SUBSCRIPTION_PRICES: dict = {
        "basic": 199,
        "pro": 399,
        "unlimited": 799
    }
    
    # Subscription limits
    SUBSCRIPTION_LIMITS: dict = {
        "free": 2,
        "basic": 50,
        "pro": 200,
        "unlimited": -1  # unlimited
    }
    
    # Calculation settings
    DEFAULT_PERIMETER_MARGIN: int = 5  # %
    DEFAULT_AREA_MARGIN: int = 10  # %
    
    # Fabric calculation settings
    FABRIC_WIDTHS: dict = {
        "1.5m": 150,  # см
        "2.0m": 200,
        "2.5m": 250, 
        "3.0m": 300,
        "5.0m": 500
    }
    DEFAULT_FABRIC_WIDTH: int = 200  # см (2 метра - самая популярная ширина)
    FABRIC_SEAM_ALLOWANCE: int = 5  # см на каждый шов
    FABRIC_EDGE_ALLOWANCE: int = 10  # см по краям
    
    # API timeouts
    GEMINI_TIMEOUT: int = 10
    IMAGE_PROCESSING_TIMEOUT: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings() 