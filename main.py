import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import settings
from bot.database.models import db
from bot.handlers import start_router, calculation_router, subscription_router
from bot.handlers.admin import router as admin_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    logger.info("Бот запускается...")
    
    # Создаем таблицы в БД
    await db.create_tables()
    logger.info("База данных инициализирована")
    
    # Получаем информацию о боте
    bot_info = await bot.get_me()
    logger.info(f"Бот @{bot_info.username} запущен!")


async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    logger.info("Бот останавливается...")
    await bot.session.close()


async def main():
    """Основная функция запуска бота"""
    # Проверяем наличие обязательных настроек
    if not settings.BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен в переменных окружения!")
        return
    
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY не установлен в переменных окружения!")
        return
    
    # Создаем бота и диспетчер
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.MARKDOWN
        )
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрируем роутеры
    dp.include_router(admin_router)  # Админские команды первыми
    dp.include_router(start_router)
    dp.include_router(calculation_router)
    dp.include_router(subscription_router)
    
    # Регистрируем хендлеры событий
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        # Запускаем бота
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем") 