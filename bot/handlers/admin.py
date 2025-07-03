from aiogram import Router, types, F
from aiogram.filters import Command
from bot.database.models import db
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

router = Router()


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    return user_id in settings.ADMIN_IDS


@router.message(Command("admin"))
async def admin_help(message: types.Message):
    """Помощь по админским командам"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    help_text = """
🔧 **АДМИНСКИЕ КОМАНДЫ**

**Управление подписками:**
/set_sub <user_id> <type> [days] - Установить подписку
/user_info <user_id> - Информация о пользователе
/unlimited <user_id> - Безлимитная подписка

**Типы подписок:**
• free - Бесплатная
• basic - Базовая (50 расчетов/мес)
• pro - Профи (200 расчетов/мес)  
• unlimited - Безлимит

**Примеры:**
/unlimited 123456789
/set_sub 123456789 pro 30
/user_info 123456789
    """
    
    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("unlimited"))
async def set_unlimited_subscription(message: types.Message):
    """Устанавливает безлимитную подписку пользователю"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    # Парсим команду
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer(
            "❌ Неверный формат команды.\n"
            "Используйте: /unlimited <user_id>"
        )
        return
    
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Неверный ID пользователя.")
        return
    
    # Устанавливаем безлимитную подписку
    success = await db.set_admin_subscription(user_id, "unlimited", 365 * 10)
    
    if success:
        await message.answer(
            f"✅ Пользователю {user_id} установлена безлимитная подписка!"
        )
        logger.info(f"Admin {message.from_user.id} set unlimited subscription for user {user_id}")
    else:
        await message.answer(
            f"❌ Ошибка при установке подписки пользователю {user_id}"
        )


@router.message(Command("set_sub"))
async def set_subscription(message: types.Message):
    """Устанавливает подписку пользователю"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    # Парсим команду
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "❌ Неверный формат команды.\n"
            "Используйте: /set_sub <user_id> <type> [days]\n\n"
            "Типы: free, basic, pro, unlimited\n"
            "По умолчанию: 365 дней"
        )
        return
    
    try:
        user_id = int(parts[1])
        sub_type = parts[2]
        days = int(parts[3]) if len(parts) > 3 else 365
    except ValueError:
        await message.answer("❌ Неверные параметры команды.")
        return
    
    # Проверяем тип подписки
    valid_types = ["free", "basic", "pro", "unlimited"]
    if sub_type not in valid_types:
        await message.answer(
            f"❌ Неверный тип подписки.\n"
            f"Доступные: {', '.join(valid_types)}"
        )
        return
    
    # Устанавливаем подписку
    success = await db.set_admin_subscription(user_id, sub_type, days)
    
    if success:
        await message.answer(
            f"✅ Пользователю {user_id} установлена подписка '{sub_type}' на {days} дней!"
        )
        logger.info(f"Admin {message.from_user.id} set {sub_type} subscription for user {user_id} for {days} days")
    else:
        await message.answer(
            f"❌ Ошибка при установке подписки пользователю {user_id}"
        )


@router.message(Command("user_info"))
async def get_user_info(message: types.Message):
    """Получает информацию о пользователе"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    # Парсим команду
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer(
            "❌ Неверный формат команды.\n"
            "Используйте: /user_info <user_id>"
        )
        return
    
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Неверный ID пользователя.")
        return
    
    # Получаем информацию о пользователе
    user_info = await db.get_user_info_admin(user_id)
    
    if not user_info:
        await message.answer(f"❌ Пользователь {user_id} не найден.")
        return
    
    # Форматируем информацию
    text = f"""
👤 **ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ**

🆔 **ID:** {user_info['telegram_id']}
👤 **Имя:** {user_info.get('first_name', 'Не указано')}
🔗 **Username:** @{user_info.get('username', 'Не указан')}

💳 **Подписка:** {user_info['subscription_type']}
📅 **Истекает:** {user_info.get('subscription_expires', 'Не указано')[:10] if user_info.get('subscription_expires') else 'Никогда'}

📊 **Статистика:**
• Всего расчетов: {user_info['total_calculations']}
• Расчетов сегодня: {user_info['daily_calculations']}
• Последний расчет: {user_info.get('last_calculation', 'Никогда')[:10] if user_info.get('last_calculation') else 'Никогда'}

💰 **Платежи:**
• Всего платежей: {user_info['total_payments']}
• Потрачено: {user_info['total_spent']:.2f} ₽

📅 **Регистрация:** {user_info['created_at'][:10]}
    """
    
    await message.answer(text.strip(), parse_mode="Markdown") 