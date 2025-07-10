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
            text="🏠 Натяжные потолки",
            callback_data="calc_type:ceiling"
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
    """Кнопка возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )
    )
    
    return builder.as_markup()


# ========== КЛАВИАТУРЫ ДЛЯ НАТЯЖНЫХ ПОТОЛКОВ ==========

def get_profile_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа профиля"""
    builder = InlineKeyboardBuilder()
    
    for key, value in settings.PROFILE_TYPES.items():
        builder.row(
            InlineKeyboardButton(
                text=value,
                callback_data=f"profile:{key}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_lighting_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа освещения"""
    builder = InlineKeyboardBuilder()
    
    for key, value in settings.LIGHTING_TYPES.items():
        builder.row(
            InlineKeyboardButton(
                text=value,
                callback_data=f"lighting:{key}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_spot_diameter_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора диаметра точечных светильников"""
    builder = InlineKeyboardBuilder()
    
    for diameter in settings.SPOT_LIGHT_DIAMETERS:
        builder.row(
            InlineKeyboardButton(
                text=f"{diameter}мм",
                callback_data=f"spot_diameter:{diameter}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Другой",
            callback_data="spot_diameter:custom"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_light_line_width_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора ширины световых линий"""
    builder = InlineKeyboardBuilder()
    
    for width in settings.LIGHT_LINE_WIDTHS:
        builder.row(
            InlineKeyboardButton(
                text=f"{width} см",
                callback_data=f"light_width:{width}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_corners_count_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора количества углов 90°"""
    builder = InlineKeyboardBuilder()
    
    # Кнопки для количества углов
    corners_options = [0, 1, 2, 3, 4]
    for i in range(0, len(corners_options), 3):  # По 3 кнопки в ряд
        row_buttons = []
        for j in range(i, min(i + 3, len(corners_options))):
            count = corners_options[j]
            row_buttons.append(
                InlineKeyboardButton(
                    text=str(count),
                    callback_data=f"corners:{count}"
                )
            )
        builder.row(*row_buttons)
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Больше",
            callback_data="corners:more"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_crossings_count_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора количества перекрестий"""
    builder = InlineKeyboardBuilder()
    
    # Кнопки для количества перекрестий
    crossing_options = [0, 1, 2, 3]
    for i in range(0, len(crossing_options), 2):  # По 2 кнопки в ряд
        row_buttons = []
        for j in range(i, min(i + 2, len(crossing_options))):
            count = crossing_options[j]
            row_buttons.append(
                InlineKeyboardButton(
                    text=str(count),
                    callback_data=f"crossings:{count}"
                )
            )
        builder.row(*row_buttons)
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Больше",
            callback_data="crossings:more"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_yes_no_keyboard(action: str) -> InlineKeyboardMarkup:
    """Универсальная клавиатура Да/Нет"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Да",
            callback_data=f"{action}:yes"
        ),
        InlineKeyboardButton(
            text="❌ Нет",
            callback_data=f"{action}:no"
        )
    )
    
    return builder.as_markup()


def get_curtain_niche_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа ниши под шторы"""
    builder = InlineKeyboardBuilder()
    
    for key, value in settings.CURTAIN_NICHE_TYPES.items():
        builder.row(
            InlineKeyboardButton(
                text=value,
                callback_data=f"curtain_type:{key}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_fastener_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа крепежа"""
    builder = InlineKeyboardBuilder()
    
    for key, value in settings.FASTENER_TYPES.items():
        builder.row(
            InlineKeyboardButton(
                text=value,
                callback_data=f"fastener:{key}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel"
        )
    )
    
    return builder.as_markup()


def get_estimate_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура действий со сметой"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📄 Скачать PDF",
            callback_data="estimate:pdf"
        ),
        InlineKeyboardButton(
            text="📊 Скачать Excel",
            callback_data="estimate:excel"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 Новый расчет",
            callback_data="estimate:new"
        ),
        InlineKeyboardButton(
            text="✏️ Редактировать",
            callback_data="estimate:edit"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )
    )
    
    return builder.as_markup() 