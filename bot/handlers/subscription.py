from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.main import (
    get_subscription_keyboard,
    get_payment_keyboard,
    get_back_to_menu_keyboard
)
from bot.database.models import db
from config.settings import settings
from datetime import datetime, timedelta
import logging
import uuid

try:
    from yookassa import Configuration, Payment
    from yookassa.domain.common import SecurityHelper
    YOOKASSA_AVAILABLE = True
    if settings.YOOKASSA_SHOP_ID and settings.YOOKASSA_SECRET_KEY:
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
except:
    YOOKASSA_AVAILABLE = False

logger = logging.getLogger(__name__)

router = Router()


class PaymentStates(StatesGroup):
    waiting_for_payment = State()


@router.message(F.text == "💳 Подписка")
async def show_subscription_menu(message: types.Message):
    """Показ меню подписок"""
    user_id = message.from_user.id
    
    # Получаем текущую подписку
    subscription = await db.get_active_subscription(user_id)
    user = await db.get_user(user_id)
    
    if subscription == 'free':
        text = "💳 **Ваш текущий план: Бесплатный**\n\n"
        text += "📊 Лимит: 2 расчета в день\n\n"
    else:
        expires = user.get('subscription_expires')
        if expires:
            expires_date = datetime.fromisoformat(expires).strftime("%d.%m.%Y")
            text = f"💳 **Ваш текущий план: {subscription.title()}**\n"
            text += f"📅 Действует до: {expires_date}\n\n"
        else:
            text = "💳 **Ваш текущий план: Бесплатный**\n\n"
    
    text += "**Доступные тарифы:**\n\n"
    text += "📦 **Базовый** - 199₽/мес\n• 50 расчетов в месяц\n• История расчетов\n• Базовая поддержка\n\n"
    text += "🚀 **Профи** - 399₽/мес\n• 200 расчетов в месяц\n• История расчетов\n• Приоритетная поддержка\n\n"
    text += "♾️ **Безлимит** - 799₽/мес\n• Неограниченно расчетов\n• История расчетов\n• VIP поддержка\n• Экспорт в PDF\n\n"
    text += "Выберите подходящий тариф:"
    
    await message.answer(
        text,
        reply_markup=get_subscription_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("subscribe:"))
async def process_subscription_choice(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора тарифа"""
    plan_type = callback.data.split(":")[1]
    
    if not YOOKASSA_AVAILABLE or not settings.YOOKASSA_SHOP_ID:
        await callback.answer(
            "❌ Платежная система временно недоступна. Обратитесь в поддержку.",
            show_alert=True
        )
        return
    
    # Создаем платеж
    price = settings.SUBSCRIPTION_PRICES[plan_type]
    plan_names = {
        'basic': 'Базовый',
        'pro': 'Профи',
        'unlimited': 'Безлимит'
    }
    
    try:
        # Создаем уникальный ID платежа
        idempotence_key = str(uuid.uuid4())
        
        payment = Payment.create({
            "amount": {
                "value": f"{price}.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/{settings.BOT_USERNAME}"
            },
            "capture": True,
            "description": f"Подписка {plan_names[plan_type]} на 1 месяц",
            "metadata": {
                "user_id": str(callback.from_user.id),
                "plan_type": plan_type
            }
        }, idempotence_key)
        
        # Сохраняем информацию о платеже
        await db.save_payment(
            user_id=callback.from_user.id,
            payment_id=payment.id,
            plan_type=plan_type,
            amount=price
        )
        
        # Сохраняем в состоянии
        await state.update_data(
            payment_id=payment.id,
            plan_type=plan_type
        )
        await state.set_state(PaymentStates.waiting_for_payment)
        
        # Отправляем ссылку на оплату
        await callback.message.edit_text(
            f"💳 **Оформление подписки**\n\n"
            f"Тариф: **{plan_names[plan_type]}**\n"
            f"Стоимость: **{price}₽**\n"
            f"Срок: 1 месяц\n\n"
            "Нажмите кнопку ниже для перехода к оплате.\n"
            "После оплаты нажмите «Проверить оплату»",
            reply_markup=get_payment_keyboard(payment.confirmation.confirmation_url),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        await callback.answer(
            "❌ Ошибка создания платежа. Попробуйте позже.",
            show_alert=True
        )
    
    await callback.answer()


@router.callback_query(F.data == "check_payment")
async def check_payment_status(callback: types.CallbackQuery, state: FSMContext):
    """Проверка статуса платежа"""
    data = await state.get_data()
    payment_id = data.get('payment_id')
    plan_type = data.get('plan_type')
    
    if not payment_id:
        await callback.answer("❌ Платеж не найден", show_alert=True)
        return
    
    try:
        # Проверяем статус платежа
        payment = Payment.find_one(payment_id)
        
        if payment.status == 'succeeded':
            # Платеж успешен, активируем подписку
            user_id = callback.from_user.id
            expires = datetime.now() + timedelta(days=30)
            
            await db.update_user_subscription(
                telegram_id=user_id,
                subscription_type=plan_type,
                expires=expires
            )
            
            await db.update_payment_status(payment_id, 'succeeded')
            
            plan_names = {
                'basic': 'Базовый',
                'pro': 'Профи',
                'unlimited': 'Безлимит'
            }
            
            await callback.message.edit_text(
                f"✅ **Платеж успешно проведен!**\n\n"
                f"Ваша подписка **{plan_names[plan_type]}** активирована.\n"
                f"Действует до: {expires.strftime('%d.%m.%Y')}\n\n"
                "Спасибо за доверие! 🎉",
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="Markdown"
            )
            
            await state.clear()
            
        elif payment.status == 'pending' or payment.status == 'waiting_for_capture':
            await callback.answer(
                "⏳ Платеж еще обрабатывается. Попробуйте через минуту.",
                show_alert=True
            )
        else:
            await callback.answer(
                f"❌ Платеж не прошел. Статус: {payment.status}",
                show_alert=True
            )
            
    except Exception as e:
        logger.error(f"Ошибка проверки платежа: {e}")
        await callback.answer(
            "❌ Ошибка проверки платежа. Обратитесь в поддержку.",
            show_alert=True
        )


# Фиктивная обработка для демо-режима (когда YooKassa не настроена)
@router.callback_query(F.data.startswith("demo_activate:"))
async def demo_activate_subscription(callback: types.CallbackQuery):
    """Демо-активация подписки для тестирования"""
    if YOOKASSA_AVAILABLE and settings.YOOKASSA_SHOP_ID:
        await callback.answer("Используйте реальную оплату", show_alert=True)
        return
    
    plan_type = callback.data.split(":")[1]
    user_id = callback.from_user.id
    expires = datetime.now() + timedelta(days=30)
    
    await db.update_user_subscription(
        telegram_id=user_id,
        subscription_type=plan_type,
        expires=expires
    )
    
    plan_names = {
        'basic': 'Базовый',
        'pro': 'Профи',
        'unlimited': 'Безлимит'
    }
    
    await callback.message.edit_text(
        f"✅ **Демо-режим: Подписка активирована!**\n\n"
        f"Тариф **{plan_names[plan_type]}** активен до {expires.strftime('%d.%m.%Y')}\n\n"
        "⚠️ Это демо-версия. В продакшене будет реальная оплата.",
        reply_markup=get_back_to_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer() 