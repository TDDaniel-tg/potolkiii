import aiosqlite
from datetime import datetime, date, timedelta
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        
    async def create_tables(self):
        """Создает таблицы в базе данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    subscription_type TEXT DEFAULT 'unlimited',
                    subscription_expires DATETIME,
                    daily_calculations INTEGER DEFAULT 0,
                    last_calculation_date DATE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица расчетов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    calculation_type TEXT NOT NULL,
                    room_type TEXT,
                    room_description TEXT,
                    measurements TEXT,
                    perimeter REAL,
                    area REAL,
                    corners_count INTEGER DEFAULT 4,
                    recognized_data TEXT,
                    final_result TEXT,
                    
                    -- Этап 2: Профиль
                    profile_type TEXT,
                    profile_quantity REAL,
                    dowel_nails_count INTEGER,
                    
                    -- Этап 3: Освещение
                    lighting_type TEXT,
                    lighting_data TEXT,  -- JSON с параметрами освещения
                    
                    -- Этап 4: Ниши под шторы
                    curtain_niche_needed BOOLEAN DEFAULT FALSE,
                    curtain_niche_type TEXT,
                    curtain_niche_meters REAL,
                    curtain_ends_count INTEGER,
                    curtain_tape_meters REAL,
                    curtain_brackets_count INTEGER,
                    curtain_screws_count INTEGER,
                    
                    -- Этап 5: Дополнительные элементы
                    timber_needed BOOLEAN DEFAULT FALSE,
                    timber_meters REAL,
                    timber_brackets_count INTEGER,
                    
                    -- Этап 6: Крепеж
                    fastener_type TEXT,
                    
                    -- Итоговые расчеты
                    total_hangers INTEGER,
                    total_dowels INTEGER,
                    total_screws INTEGER,
                    glue_volume REAL,
                    
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
                )
            """)
            
            # Добавляем новые колонки если их нет (для существующих баз)
            try:
                await db.execute("ALTER TABLE calculations ADD COLUMN room_type TEXT")
                await db.execute("ALTER TABLE calculations ADD COLUMN room_description TEXT")
                await db.execute("ALTER TABLE calculations ADD COLUMN measurements TEXT")
                await db.execute("ALTER TABLE calculations ADD COLUMN perimeter REAL")
                await db.execute("ALTER TABLE calculations ADD COLUMN area REAL")
                await db.execute("ALTER TABLE calculations ADD COLUMN corners_count INTEGER DEFAULT 4")
                
                # Новые поля для натяжных потолков
                await db.execute("ALTER TABLE calculations ADD COLUMN profile_type TEXT")
                await db.execute("ALTER TABLE calculations ADD COLUMN profile_quantity REAL")
                await db.execute("ALTER TABLE calculations ADD COLUMN dowel_nails_count INTEGER")
                
                await db.execute("ALTER TABLE calculations ADD COLUMN lighting_type TEXT")
                await db.execute("ALTER TABLE calculations ADD COLUMN lighting_data TEXT")
                
                await db.execute("ALTER TABLE calculations ADD COLUMN curtain_niche_needed BOOLEAN DEFAULT FALSE")
                await db.execute("ALTER TABLE calculations ADD COLUMN curtain_niche_type TEXT")
                await db.execute("ALTER TABLE calculations ADD COLUMN curtain_niche_meters REAL")
                await db.execute("ALTER TABLE calculations ADD COLUMN curtain_ends_count INTEGER")
                await db.execute("ALTER TABLE calculations ADD COLUMN curtain_tape_meters REAL")
                await db.execute("ALTER TABLE calculations ADD COLUMN curtain_brackets_count INTEGER")
                await db.execute("ALTER TABLE calculations ADD COLUMN curtain_screws_count INTEGER")
                
                await db.execute("ALTER TABLE calculations ADD COLUMN timber_needed BOOLEAN DEFAULT FALSE")
                await db.execute("ALTER TABLE calculations ADD COLUMN timber_meters REAL")
                await db.execute("ALTER TABLE calculations ADD COLUMN timber_brackets_count INTEGER")
                
                await db.execute("ALTER TABLE calculations ADD COLUMN fastener_type TEXT")
                
                await db.execute("ALTER TABLE calculations ADD COLUMN total_hangers INTEGER")
                await db.execute("ALTER TABLE calculations ADD COLUMN total_dowels INTEGER")
                await db.execute("ALTER TABLE calculations ADD COLUMN total_screws INTEGER")
                await db.execute("ALTER TABLE calculations ADD COLUMN glue_volume REAL")
            except:
                # Колонки уже существуют
                pass
            
            # Таблица платежей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    payment_id TEXT UNIQUE NOT NULL,
                    plan_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
                )
            """)
            
            await db.commit()
    
    async def get_user(self, telegram_id: int) -> Optional[dict]:
        """Получает пользователя по telegram_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE telegram_id = ?", 
                (telegram_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_user(self, telegram_id: int, username: str = None, 
                         first_name: str = None) -> dict:
        """Создает нового пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_calculation_date)
                VALUES (?, ?, ?, ?)
            """, (telegram_id, username, first_name, date.today()))
            await db.commit()
            
        return await self.get_user(telegram_id)
    
    async def update_user_subscription(self, telegram_id: int, 
                                     subscription_type: str, 
                                     expires: datetime):
        """Обновляет подписку пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users 
                SET subscription_type = ?, subscription_expires = ?
                WHERE telegram_id = ?
            """, (subscription_type, expires, telegram_id))
            await db.commit()
    
    async def get_user_calculations_today(self, telegram_id: int) -> int:
        """Получает количество расчетов пользователя за сегодня"""
        async with aiosqlite.connect(self.db_path) as db:
            # Сначала проверяем и обновляем дату последнего расчета
            cursor = await db.execute(
                "SELECT last_calculation_date, daily_calculations FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                last_date = datetime.strptime(row[0], "%Y-%m-%d").date() if row[0] else None
                today = date.today()
                
                if last_date != today:
                    # Сбрасываем счетчик для нового дня
                    await db.execute("""
                        UPDATE users 
                        SET daily_calculations = 0, last_calculation_date = ?
                        WHERE telegram_id = ?
                    """, (today, telegram_id))
                    await db.commit()
                    return 0
                else:
                    return row[1]
            
            return 0
    
    async def increment_user_calculations(self, telegram_id: int):
        """Увеличивает счетчик расчетов пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users 
                SET daily_calculations = daily_calculations + 1
                WHERE telegram_id = ?
            """, (telegram_id,))
            await db.commit()
    
    async def save_calculation(self, user_id: int, calculation_type: str,
                             room_type: str = None, room_description: str = None,
                             measurements: list = None, perimeter: float = None,
                             area: float = None, corners_count: int = 4,
                             recognized_data: dict = None, final_result: dict = None,
                             # Этап 2: Профиль
                             profile_type: str = None, profile_quantity: float = None,
                             dowel_nails_count: int = None,
                             # Этап 3: Освещение
                             lighting_type: str = None, lighting_data: dict = None,
                             # Этап 4: Ниши под шторы
                             curtain_niche_needed: bool = False, curtain_niche_type: str = None,
                             curtain_niche_meters: float = None, curtain_ends_count: int = None,
                             curtain_tape_meters: float = None, curtain_brackets_count: int = None,
                             curtain_screws_count: int = None,
                             # Этап 5: Дополнительные элементы
                             timber_needed: bool = False, timber_meters: float = None,
                             timber_brackets_count: int = None,
                             # Этап 6: Крепеж
                             fastener_type: str = None,
                             # Итоговые расчеты
                             total_hangers: int = None, total_dowels: int = None,
                             total_screws: int = None, glue_volume: float = None):
        """Сохраняет расчет в базу данных"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO calculations (
                    user_id, calculation_type, room_type, room_description,
                    measurements, perimeter, area, corners_count, recognized_data, final_result,
                    profile_type, profile_quantity, dowel_nails_count,
                    lighting_type, lighting_data,
                    curtain_niche_needed, curtain_niche_type, curtain_niche_meters,
                    curtain_ends_count, curtain_tape_meters, curtain_brackets_count, curtain_screws_count,
                    timber_needed, timber_meters, timber_brackets_count,
                    fastener_type,
                    total_hangers, total_dowels, total_screws, glue_volume
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, 
                calculation_type,
                room_type,
                room_description,
                json.dumps(measurements, ensure_ascii=False) if measurements else None,
                perimeter,
                area,
                corners_count,
                json.dumps(recognized_data, ensure_ascii=False) if recognized_data else None,
                json.dumps(final_result, ensure_ascii=False) if final_result else None,
                profile_type,
                profile_quantity,
                dowel_nails_count,
                lighting_type,
                json.dumps(lighting_data, ensure_ascii=False) if lighting_data else None,
                curtain_niche_needed,
                curtain_niche_type,
                curtain_niche_meters,
                curtain_ends_count,
                curtain_tape_meters,
                curtain_brackets_count,
                curtain_screws_count,
                timber_needed,
                timber_meters,
                timber_brackets_count,
                fastener_type,
                total_hangers,
                total_dowels,
                total_screws,
                glue_volume
            ))
            await db.commit()
    
    async def get_user_calculations(self, telegram_id: int, limit: int = 10) -> list:
        """Получает последние расчеты пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM calculations 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (telegram_id, limit))
            
            rows = await cursor.fetchall()
            calculations = []
            
            for row in rows:
                calc = dict(row)
                # Парсим JSON поля
                if calc['measurements']:
                    try:
                        calc['measurements'] = json.loads(calc['measurements'])
                    except:
                        calc['measurements'] = []
                        
                if calc['recognized_data']:
                    try:
                        calc['recognized_data'] = json.loads(calc['recognized_data'])
                    except:
                        calc['recognized_data'] = {}
                        
                if calc['final_result']:
                    try:
                        calc['final_result'] = json.loads(calc['final_result'])
                    except:
                        calc['final_result'] = {}
                        
                if calc['lighting_data']:
                    try:
                        calc['lighting_data'] = json.loads(calc['lighting_data'])
                    except:
                        calc['lighting_data'] = {}
                        
                calculations.append(calc)
            
            return calculations
    
    async def save_payment(self, user_id: int, payment_id: str, 
                          plan_type: str, amount: float):
        """Сохраняет информацию о платеже"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO payments (user_id, payment_id, plan_type, amount)
                VALUES (?, ?, ?, ?)
            """, (user_id, payment_id, plan_type, amount))
            await db.commit()
    
    async def update_payment_status(self, payment_id: str, status: str):
        """Обновляет статус платежа"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE payments 
                SET status = ?
                WHERE payment_id = ?
            """, (status, payment_id))
            await db.commit()
    
    async def get_active_subscription(self, telegram_id: int) -> Optional[str]:
        """Проверяет активную подписку пользователя"""
        user = await self.get_user(telegram_id)
        if not user:
            return None
            
        if user['subscription_type'] == 'free':
            return 'free'
            
        if user['subscription_expires']:
            expires = datetime.fromisoformat(user['subscription_expires'])
            if expires > datetime.now():
                return user['subscription_type']
            else:
                # Подписка истекла, сбрасываем на бесплатную
                await self.update_user_subscription(telegram_id, 'free', None)
                return 'free'
        
        return 'free'
    
    async def set_admin_subscription(self, telegram_id: int, subscription_type: str, 
                                   duration_days: int = 365) -> bool:
        """
        Устанавливает подписку пользователю (админская функция)
        
        Args:
            telegram_id: ID пользователя
            subscription_type: Тип подписки (basic, pro, unlimited)
            duration_days: Продолжительность в днях (по умолчанию год)
        
        Returns:
            True если успешно, False если ошибка
        """
        try:
            # Создаем пользователя если его нет
            user = await self.get_user(telegram_id)
            if not user:
                await self.create_user(telegram_id)
            
            # Рассчитываем дату окончания
            if subscription_type == 'unlimited':
                # Для безлимита ставим далекую дату
                expires = datetime.now() + timedelta(days=365 * 10)  # 10 лет
            else:
                expires = datetime.now() + timedelta(days=duration_days)
            
            # Обновляем подписку
            await self.update_user_subscription(telegram_id, subscription_type, expires)
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при установке подписки админом: {e}")
            return False
    
    async def get_user_info_admin(self, telegram_id: int) -> Optional[dict]:
        """Получает подробную информацию о пользователе для админа"""
        user = await self.get_user(telegram_id)
        if not user:
            return None
        
        # Получаем статистику
        async with aiosqlite.connect(self.db_path) as db:
            # Количество расчетов
            cursor = await db.execute(
                "SELECT COUNT(*) FROM calculations WHERE user_id = ?",
                (telegram_id,)
            )
            total_calculations = (await cursor.fetchone())[0]
            
            # Последний расчет
            cursor = await db.execute(
                "SELECT created_at FROM calculations WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (telegram_id,)
            )
            last_calc = await cursor.fetchone()
            last_calculation = last_calc[0] if last_calc else None
            
            # Платежи
            cursor = await db.execute(
                "SELECT COUNT(*), SUM(amount) FROM payments WHERE user_id = ? AND status = 'succeeded'",
                (telegram_id,)
            )
            payment_data = await cursor.fetchone()
            total_payments = payment_data[0] or 0
            total_spent = payment_data[1] or 0
        
        return {
            **user,
            'total_calculations': total_calculations,
            'last_calculation': last_calculation,
            'total_payments': total_payments,
            'total_spent': total_spent
        }


# Создаем экземпляр базы данных
db = Database() 