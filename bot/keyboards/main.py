from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config.settings import settings


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="📐 Рассчитать размеры")
    )
    builder.row(
        KeyboardButton(text="💳 Подписка"),
        KeyboardButton(text="📊 Мои расчеты")
    )
    builder.row(
        KeyboardButton(text="ℹ️ Помощь")
    )
    
    return builder.as_markup(resize_keyboard=True)


def get_calculation_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа расчета"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📐 Периметр (плинтус/багет)",
            callback_data="calc_type:perimeter"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📏 Площадь (полотно)",
            callback_data="calc_type:area"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🧵 Ткань (метры)",
            callback_data="calc_type:fabric"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📐📏 Полный расчет",
            callback_data="calc_type:both"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎯 Все + ткань",
            callback_data="calc_type:complete"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_fabric_width_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора ширины рулона ткани"""
    builder = InlineKeyboardBuilder()
    
    # Создаем кнопки для каждой ширины ткани
    for width_name, width_cm in settings.FABRIC_WIDTHS.items():
        builder.row(
            InlineKeyboardButton(
                text=f"📏 {width_name} ({width_cm} см)",
                callback_data=f"fabric_width:{width_cm}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора тарифного плана"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📦 Базовый - 199₽/мес",
            callback_data="subscribe:basic"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🚀 Профи - 399₽/мес",
            callback_data="subscribe:pro"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="♾️ Безлимит - 799₽/мес",
            callback_data="subscribe:unlimited"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения распознанных размеров"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Правильно",
            callback_data="confirm_measurements"
        ),
        InlineKeyboardButton(
            text="✏️ Исправить",
            callback_data="edit_measurements"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_confirmation_with_fabric_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения с возможностью изменить ширину ткани"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Правильно",
            callback_data="confirm_measurements"
        ),
        InlineKeyboardButton(
            text="✏️ Исправить",
            callback_data="edit_measurements"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🧵 Изменить ширину ткани",
            callback_data="change_fabric_width"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_manual_input_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ручного ввода"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Ввести размеры вручную",
            callback_data="manual_input"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📷 Попробовать другое фото",
            callback_data="retry_photo"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    """Клавиатура для оплаты"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="💳 Оплатить",
            url=payment_url
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="✅ Проверить оплату",
            callback_data="check_payment"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🏠 В главное меню",
            callback_data="main_menu"
        )
    )
    
    return builder.as_markup() 