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
    
    # Натяжные потолки - типы профилей
    PROFILE_TYPES: dict = {
        "plastic_basic": "🔲 Пластиковый базовый",
        "shadow_plastic": "🔳 Теневой пластиковый", 
        "shadow_aluminum": "⬛️ Теневой алюминиевый"
    }
    
    # Освещение - типы
    LIGHTING_TYPES: dict = {
        "chandelier": "💡 Люстра",
        "spot_lights": "🔆 Точечные светильники",
        "light_lines": "📏 Световые линии", 
        "floating_light": "✨ Парящая подсветка",
        "combined": "➕ Комбинированное",
        "none": "❌ Без освещения"
    }
    
    # Диаметры точечных светильников
    SPOT_LIGHT_DIAMETERS: List[int] = [50, 65, 85]  # мм
    
    # Ширины световых линий
    LIGHT_LINE_WIDTHS: List[int] = [3, 5]  # см
    
    # Типы ниш под шторы
    CURTAIN_NICHE_TYPES: dict = {
        "l_shaped": "🔤 Г-образная",
        "u_shaped": "🔠 П-образная"
    }
    
    # Типы крепежа
    FASTENER_TYPES: dict = {
        "dowel_nails": "🔩 Дюбель-гвозди",
        "regular_dowels": "🔧 Обычные дюбели",
        "red_dowels": "🔴 Красные дюбели"
    }
    
    # Расчетные коэффициенты
    CALCULATION_COEFFICIENTS: dict = {
        # Профиль
        "profile_margin": 0.05,  # 5% запас на подрезку
        "dowel_nails_per_meter": 3.33,  # 1 дюбель каждые 30 см (1/0.3)
        
        # Подвесы
        "hangers_per_sqm": 0.5,  # 1 подвес на 2 м²
        "hangers_per_spotlight": 2,  # 2 подвеса на светильник
        
        # Световые линии
        "light_line_corner_margin": 0.1,  # 10 см на угол
        "light_line_cross_margin": 0.2,  # 20 см на перекрестье
        "diffuser_margin": 0.05,  # 5% запас на рассеиватель
        
        # Парящая подсветка
        "floating_diffuser_margin": 0.05,  # 5% запас
        "floating_screws_per_meter": 3,  # 3 самореза на метр
        
        # Ниши под шторы
        "curtain_tape_per_meter": 2,  # 2м ленты на 1м профиля
        "curtain_brackets_per_meter": 2,  # 2 кронштейна на метр
        "curtain_screws_per_bracket": 2,  # 2 самореза на кронштейн
        "curtain_ends_count": 2,  # торцы для П-образной
        
        # Брус
        "timber_brackets_per_meter": 2,  # 2 кронштейна на метр
        
        # Общие расчеты
        "screws_per_perimeter_meter": 4,  # 4 самореза на метр периметра
        "glue_ml_per_hanger": 20,  # 20 мл клея на подвес
    }
    
    # API timeouts
    GEMINI_TIMEOUT: int = 10
    IMAGE_PROCESSING_TIMEOUT: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings() 