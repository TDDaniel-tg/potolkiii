from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.main import (
    get_calculation_type_keyboard,
    get_confirmation_keyboard,
    get_confirmation_with_fabric_keyboard,
    get_fabric_width_keyboard,
    get_manual_input_keyboard,
    get_back_to_menu_keyboard,
    get_main_keyboard,
    # Новые клавиатуры для натяжных потолков
    get_profile_type_keyboard,
    get_lighting_type_keyboard,
    get_spot_diameter_keyboard,
    get_light_line_width_keyboard,
    get_corners_count_keyboard,
    get_crossings_count_keyboard,
    get_yes_no_keyboard,
    get_curtain_niche_type_keyboard,
    get_fastener_type_keyboard,
    get_estimate_keyboard
)
from bot.database.models import db
from bot.utils.gemini_api import recognizer
from bot.utils.calculator import calculator
from bot.utils.ceiling_calculator import ceiling_calc
from bot.utils.image_processor import image_processor
from config.settings import settings
import logging
import io
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = Router()


class CalculationStates(StatesGroup):
    choosing_type = State()
    waiting_for_photo = State()
    confirming_measurements = State()
    manual_input = State()
    
    # Новые состояния для натяжных потолков
    choosing_profile = State()
    choosing_lighting = State()
    spot_diameter_input = State()
    spot_count_input = State()
    light_lines_width = State()
    light_lines_meters = State()
    light_lines_corners = State()
    light_lines_crossings = State()
    floating_light_meters = State()
    curtain_niche_choice = State()
    curtain_niche_type = State()
    curtain_niche_meters = State()
    timber_choice = State()
    timber_meters = State()
    fastener_choice = State()
    custom_diameter_input = State()
    custom_corners_input = State()
    custom_crossings_input = State()


@router.message(F.text == "📐 Рассчитать размеры")
async def start_calculation(message: types.Message, state: FSMContext):
    """Начало процесса расчета"""
    # Проверяем лимиты пользователя
    user_id = message.from_user.id
    
    # Получаем активную подписку
    subscription = await db.get_active_subscription(user_id)
    calculations_today = await db.get_user_calculations_today(user_id)
    
    # Проверяем лимиты
    limit = settings.SUBSCRIPTION_LIMITS.get(subscription, 2)
    
    if subscription == 'free' and calculations_today >= limit:
        await message.answer(
            "❌ Вы исчерпали дневной лимит бесплатных расчетов (2 в день).\n\n"
            "💳 Оформите подписку для продолжения работы:\n"
            "• Базовый - 50 расчетов/месяц (199₽)\n"
            "• Профи - 200 расчетов/месяц (399₽)\n"
            "• Безлимит - неограниченно (799₽)\n\n"
            "Нажмите «💳 Подписка» в главном меню."
        )
        return
    
    elif subscription != 'unlimited' and subscription != 'free':
        # Для платных подписок проверяем месячный лимит
        # TODO: добавить проверку месячного лимита
        pass
    
    await state.set_state(CalculationStates.choosing_type)
    await message.answer(
        "Выберите тип расчета:",
        reply_markup=get_calculation_type_keyboard()
    )


@router.callback_query(F.data.startswith("calc_type:"))
async def process_calculation_type(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа расчета"""
    calc_type = callback.data.split(":")[1]
    
    await state.update_data(calculation_type=calc_type)
    
    type_text = {
        "perimeter": "📐 Расчет периметра",
        "area": "📏 Расчет площади", 
        "fabric": "🧵 Расчет ткани",
        "both": "📐📏 Полный расчет",
        "complete": "🎯 Комплексный расчет",
        "ceiling": "🏠 Натяжные потолки"
    }
    
    # Если нужен расчет ткани, сначала выбираем ширину рулона
    if calc_type in ['fabric', 'complete']:
        await callback.message.edit_text(
            f"{type_text[calc_type]}\n\n"
            "🧵 Выберите ширину рулона ткани:",
            reply_markup=get_fabric_width_keyboard()
        )
    else:
        # Переходим сразу к загрузке фото
        await state.set_state(CalculationStates.waiting_for_photo)
        
        if calc_type == "ceiling":
            # Для натяжных потолков специальное сообщение
            await callback.message.edit_text(
                f"{type_text[calc_type]}\n\n"
                "📸 Отправьте фото с замерами помещения.\n\n"
                "💡 Подсказки:\n"
                "• Укажите длину и ширину комнаты\n"
                "• Если комната сложной формы - размеры всех сторон\n"
                "• Количество углов в помещении\n"
                "• Фото должно быть четким и разборчивым",
                reply_markup=get_manual_input_keyboard()
            )
        else:
            await callback.message.edit_text(
                f"{type_text[calc_type]}\n\n"
                "📸 Отправьте фото с замерами помещения.\n\n"
                "💡 Подсказки:\n"
                "• Фото должно быть четким\n"
                "• Размеры должны быть хорошо видны\n"
                "• Можно отправить фото рукописного чертежа",
                reply_markup=get_manual_input_keyboard()
            )
    
    await callback.answer()


@router.callback_query(F.data.startswith("fabric_width:"))
async def process_fabric_width(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора ширины ткани"""
    fabric_width = int(callback.data.split(":")[1])
    data = await state.get_data()
    calc_type = data.get('calculation_type', 'fabric')
    
    await state.update_data(fabric_width=fabric_width)
    await state.set_state(CalculationStates.waiting_for_photo)
    
    type_text = {
        "fabric": "🧵 Расчет ткани",
        "complete": "🎯 Комплексный расчет"
    }
    
    await callback.message.edit_text(
        f"{type_text[calc_type]}\n"
        f"🧵 Ширина рулона: {fabric_width} см\n\n"
        "📸 Отправьте фото с замерами помещения.\n\n"
        "💡 Подсказки:\n"
        "• Фото должно быть четким\n"
        "• Размеры должны быть хорошо видны\n"
        "• Можно отправить фото рукописного чертежа",
        reply_markup=get_manual_input_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "change_fabric_width")
async def change_fabric_width(callback: types.CallbackQuery, state: FSMContext):
    """Изменение ширины ткани"""
    await callback.message.edit_text(
        "🧵 Выберите новую ширину рулона ткани:",
        reply_markup=get_fabric_width_keyboard()
    )
    await callback.answer()


@router.message(CalculationStates.waiting_for_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    """Обработка фотографии с замерами"""
    await message.answer("⏳ Обрабатываю изображение...")
    
    try:
        # Получаем фото в максимальном качестве
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        
        # Скачиваем фото
        photo_bytes = io.BytesIO()
        await message.bot.download_file(file.file_path, photo_bytes)
        photo_data = photo_bytes.getvalue()
        
        # Валидируем изображение
        is_valid, error_msg = await image_processor.validate_image(photo_data)
        if not is_valid:
            await message.answer(
                f"❌ {error_msg}\n\n"
                "Попробуйте отправить другое фото или введите размеры вручную.",
                reply_markup=get_manual_input_keyboard()
            )
            return
        
        # Обрабатываем изображение
        processed_image = await image_processor.process_image(photo_data)
        if not processed_image:
            await message.answer(
                "❌ Не удалось обработать изображение.\n\n"
                "Попробуйте отправить другое фото или введите размеры вручную.",
                reply_markup=get_manual_input_keyboard()
            )
            return
        
        # Распознаем размеры
        await message.answer("🤖 Распознаю размеры...")
        recognition_result = await recognizer.recognize_measurements(processed_image)
        
        if not recognition_result or not await recognizer.validate_recognition(recognition_result):
            await message.answer(
                "❌ Не удалось распознать размеры на фото.\n\n"
                "Возможные причины:\n"
                "• Размеры плохо видны\n"
                "• Слишком много лишней информации\n"
                "• Нечеткое изображение\n\n"
                "Попробуйте другое фото или введите размеры вручную.",
                reply_markup=get_manual_input_keyboard()
            )
            return
        
        # Сохраняем результат распознавания
        await state.update_data(recognition_data=recognition_result)
        
        # Показываем распознанные размеры
        formatted_text = recognizer.format_measurements_text(recognition_result)
        
        # Выбираем подходящую клавиатуру
        data = await state.get_data()
        calc_type = data.get('calculation_type', 'both')
        
        if calc_type in ['fabric', 'complete']:
            keyboard = get_confirmation_with_fabric_keyboard()
        else:
            keyboard = get_confirmation_keyboard()
        
        await message.answer(
            f"✅ Размеры распознаны!\n\n{formatted_text}\n\n"
            "Все правильно?",
            reply_markup=keyboard
        )
        
        await state.set_state(CalculationStates.confirming_measurements)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке фото.\n\n"
            "Попробуйте еще раз или введите размеры вручную.",
            reply_markup=get_manual_input_keyboard()
        )


@router.callback_query(F.data == "manual_input")
async def start_manual_input(callback: types.CallbackQuery, state: FSMContext):
    """Начало ручного ввода размеров"""
    await state.set_state(CalculationStates.manual_input)
    
    data = await state.get_data()
    calc_type = data.get('calculation_type', 'both')
    fabric_width = data.get('fabric_width')
    
    # Формируем примеры в зависимости от типа расчета
    if calc_type in ['fabric', 'complete']:
        if fabric_width:
            fabric_info = f"🧵 Ширина рулона: {fabric_width} см\n"
        else:
            fabric_info = "🧵 Расчет ткани включен\n"
    else:
        fabric_info = ""
    
    example = "3.5 x 2.8" if calc_type in ['perimeter', 'area', 'fabric', 'both', 'complete'] else "3.5 2.8 3.5 2.8"
    
    type_names = {
        'perimeter': 'периметра',
        'area': 'площади',
        'fabric': 'ткани',
        'both': 'периметра и площади',
        'complete': 'полного расчета'
    }
    
    await callback.message.edit_text(
        f"📝 **Ручной ввод размеров**\n"
        f"🎯 Тип расчета: {type_names.get(calc_type, 'универсальный')}\n"
        f"{fabric_info}\n"
        f"Введите размеры помещения в метрах или сантиметрах.\n\n"
        f"**Примеры:**\n"
        f"• Прямоугольник: `{example}`\n"
        f"• Прямоугольник: `350 280` (в см)\n"
        f"• Сложная форма: `3.5 2.8 1.2 0.9 2.3 1.9`\n\n"
        "Числа можно разделять пробелами, запятыми или знаком x",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(CalculationStates.manual_input)
async def process_manual_input(message: types.Message, state: FSMContext):
    """Обработка ручного ввода размеров"""
    data = await state.get_data()
    calc_type = data.get('calculation_type', 'both')
    
    # Парсим введенные размеры
    recognition_data = calculator.parse_manual_input(message.text, calc_type)
    
    if not recognition_data:
        await message.answer(
            "❌ Не удалось распознать размеры.\n\n"
            "Убедитесь, что вы ввели числа.\n"
            "Примеры правильного ввода:\n"
            "• `3.5 x 2.8`\n"
            "• `350 280`\n"
            "• `3.5 2.8 1.2 0.9`",
            parse_mode="Markdown"
        )
        return
    
    # Сохраняем результат распознавания
    await state.update_data(recognition_data=recognition_data)
    
    # Показываем распознанные размеры
    formatted_text = recognizer.format_measurements_text(recognition_data)
    
    # Выбираем подходящую клавиатуру
    calc_type = data.get('calculation_type', 'both')
    
    if calc_type in ['fabric', 'complete']:
        keyboard = get_confirmation_with_fabric_keyboard()
    else:
        keyboard = get_confirmation_keyboard()
    
    await message.answer(
        f"✅ Размеры обработаны!\n\n{formatted_text}\n\n"
        "Все правильно?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    await state.set_state(CalculationStates.confirming_measurements)


@router.callback_query(F.data == "confirm_measurements")
async def confirm_and_calculate(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение распознанных размеров и выполнение расчета"""
    data = await state.get_data()
    recognition_data = data.get('recognition_data')
    calc_type = data.get('calculation_type', 'both')
    fabric_width = data.get('fabric_width')
    user_id = callback.from_user.id
    
    if not recognition_data:
        await callback.message.edit_text(
            "❌ Данные о размерах потеряны. Начните заново.",
            reply_markup=get_back_to_menu_keyboard()
        )
        await callback.answer()
        return
    
    try:
        # Проверяем, есть ли несколько помещений
        rooms = recognition_data.get('rooms', [])
        if not rooms:
            # Старый формат - конвертируем в новый
            if 'room_type' in recognition_data and 'measurements' in recognition_data:
                recognition_data = {
                    'rooms': [{
                        'room_number': 1,
                        'room_type': recognition_data['room_type'],
                        'measurements': recognition_data['measurements'],
                        'position': 'единственное помещение',
                        'confidence': recognition_data.get('confidence', 0.95)
                    }],
                    'total_rooms_found': 1
                }
                rooms = recognition_data['rooms']
        
        # Для натяжных потолков переходим к этапу выбора профиля
        if calc_type == "ceiling":
            # Проверяем, что есть данные о площади и периметре
            room = rooms[0] if rooms else {}
            measurements = room.get('measurements', [])
            
            if not measurements:
                await callback.message.edit_text(
                    "❌ Не удалось определить размеры помещения.",
                    reply_markup=get_back_to_menu_keyboard()
                )
                await callback.answer()
                return
            
            # Рассчитываем базовые параметры
            room_type = room.get('room_type', 'rectangle')
            perimeter = calculator.calculate_perimeter(measurements, room_type)
            area = calculator.calculate_area(measurements, room_type)
            
            # Сохраняем базовые данные для дальнейших расчетов
            await state.update_data(
                perimeter=perimeter / 100,  # в метрах
                area=area / 10000,  # в м²
                measurements=measurements,
                room_type=room_type,
                corners_count=len(measurements) if room_type != 'rectangle' else 4
            )
            
            # Переходим к выбору профиля
            await state.set_state(CalculationStates.choosing_profile)
            await callback.message.edit_text(
                f"✅ Размеры обработаны!\n\n"
                f"📐 Периметр: {perimeter/100:.2f} м\n"
                f"📏 Площадь: {area/10000:.2f} м²\n\n"
                f"**Этап 2: Выбор профиля**\n\n"
                f"Выберите тип профиля:",
                reply_markup=get_profile_type_keyboard(),
                parse_mode="Markdown"
            )
            await callback.answer()
            return
        
        # Выполняем расчеты для всех помещений (для остальных типов)
        results = calculator.calculate_multiple_rooms(recognition_data, calc_type, fabric_width)
        
        if not results:
            await callback.message.edit_text(
                "❌ Не удалось выполнить расчеты.",
                reply_markup=get_back_to_menu_keyboard()
            )
            await callback.answer()
            return
        
        # Форматируем результат
        result_text = calculator.format_multiple_results_text(results, calc_type)
        
        # Сохраняем результаты в базу данных
        for result in results:
            room_number = result.get('room_number', 1)
            position = result.get('position', 'неизвестно')
            
            # Создаем описание помещения
            room_description = f"Помещение #{room_number} ({position})"
            
            await db.save_calculation(
                user_id=user_id,
                calculation_type=calc_type,
                room_type=result.get('room_type'),
                measurements=result.get('measurements', []),
                perimeter=result.get('perimeter', {}).get('value_m'),
                area=result.get('area', {}).get('value_m2'),
                room_description=room_description
            )
        
        # Увеличиваем счетчик использований
        await db.increment_user_calculations(user_id)
        
        # Отправляем результат
        # Если текст слишком длинный, разбиваем на части
        if len(result_text) > 4000:
            # Разбиваем по помещениям
            parts = result_text.split('='*30)
            header = parts[0]
            
            await callback.message.edit_text(
                header + "\n📝 Результаты отправлены отдельными сообщениями...",
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="Markdown"
            )
            
            # Отправляем каждое помещение отдельно
            for i, part in enumerate(parts[1:], 1):
                if part.strip():
                    room_text = f"{'='*30}{part}"
                    if len(room_text) > 4000:
                        # Если и одно помещение слишком длинное, обрезаем
                        room_text = room_text[:3900] + "\n...\n(данные обрезаны)"
                    
                    await callback.message.answer(
                        room_text,
                        parse_mode="Markdown"
                    )
            
            # Отправляем итоги если они есть
            if "ИТОГО ПО ВСЕМ ПОМЕЩЕНИЯМ" in result_text:
                summary_start = result_text.find("📊 **ИТОГО ПО ВСЕМ ПОМЕЩЕНИЯМ:**")
                if summary_start != -1:
                    summary = result_text[summary_start:]
                    await callback.message.answer(
                        summary,
                        parse_mode="Markdown"
                    )
        else:
            await callback.message.edit_text(
                result_text,
                reply_markup=get_back_to_menu_keyboard(),
                parse_mode="Markdown"
            )
        
        # Очищаем состояние
        await state.clear()
        await callback.answer("✅ Расчет выполнен!")
        
    except Exception as e:
        logger.error(f"Ошибка при расчете: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при выполнении расчета.\nПопробуйте еще раз.",
            reply_markup=get_back_to_menu_keyboard()
        )
        await callback.answer()


@router.callback_query(F.data == "edit_measurements")
async def edit_measurements(callback: types.CallbackQuery, state: FSMContext):
    """Переход к ручному вводу для корректировки"""
    await start_manual_input(callback, state)


@router.callback_query(F.data == "retry_photo")
async def retry_photo(callback: types.CallbackQuery, state: FSMContext):
    """Повторная отправка фото"""
    await state.set_state(CalculationStates.waiting_for_photo)
    await callback.message.edit_text(
        "📸 Отправьте новое фото с замерами помещения.",
        reply_markup=get_manual_input_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_calculation(callback: types.CallbackQuery, state: FSMContext):
    """Отмена расчета"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ Расчет отменен.\n\nВыберите действие в меню:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.message(F.text == "📊 Мои расчеты")
async def show_calculations_history(message: types.Message):
    """Показ истории расчетов"""
    user_id = message.from_user.id
    
    # Проверяем подписку
    subscription = await db.get_active_subscription(user_id)
    if subscription == 'free':
        await message.answer(
            "📊 История расчетов доступна только для подписчиков.\n\n"
            "💳 Оформите подписку для доступа к:\n"
            "• Истории всех расчетов\n"
            "• Экспорту результатов\n"
            "• Приоритетной поддержке"
        )
        return
    
    # Получаем последние расчеты
    calculations = await db.get_user_calculations(user_id, limit=20)
    
    if not calculations:
        await message.answer("У вас пока нет сохраненных расчетов.")
        return
    
    text = "📊 **Ваши последние расчеты:**\n\n"
    
    # Группируем расчеты по дате
    grouped_by_date = {}
    
    for calc in calculations:
        date_str = calc['created_at'][:10]  # YYYY-MM-DD
        if date_str not in grouped_by_date:
            grouped_by_date[date_str] = []
        grouped_by_date[date_str].append(calc)
    
    total_calculations = 0
    
    # Выводим по датам
    for date_str in sorted(grouped_by_date.keys(), reverse=True):
        date_calcs = grouped_by_date[date_str]
        
        # Форматируем дату
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d.%m.%Y")
        except:
            formatted_date = date_str
        
        text += f"📅 **{formatted_date}** ({len(date_calcs)} расчетов)\n"
        
        for calc in date_calcs:
            total_calculations += 1
            
            # Определяем тип расчета
            calc_type = calc.get('calculation_type', 'both')
            type_emoji = {
                'perimeter': '📐',
                'area': '📏', 
                'both': '📐📏'
            }
            
            # Описание помещения
            room_desc = calc.get('room_description', 'Помещение')
            room_type = calc.get('room_type', 'rectangle')
            room_type_text = 'Прямоугольник' if room_type == 'rectangle' else 'Сложная форма'
            
            text += f"  {type_emoji.get(calc_type, '📊')} {room_desc}\n"
            text += f"     🏠 {room_type_text}"
            
            # Результаты
            if calc.get('perimeter'):
                text += f" | 📐 {calc['perimeter']:.1f}м"
            
            if calc.get('area'):
                text += f" | 📏 {calc['area']:.1f}м²"
            
            # Время
            time_str = calc['created_at'][11:16]  # HH:MM
            text += f" | ⏰ {time_str}"
            
            text += "\n"
        
        text += "\n"
        
        # Ограничение длины сообщения
        if len(text) > 3500:
            text += f"... и еще {len(calculations) - total_calculations} расчетов\n\n"
            text += "💡 Полная история доступна в веб-интерфейсе (скоро)"
            break
    
    if total_calculations > 0:
        text += f"📈 **Всего расчетов показано:** {total_calculations}\n"
        text += f"🎯 **Ваша подписка:** {subscription.title()}"
    
    await message.answer(text, parse_mode="Markdown") 


# ========== ОБРАБОТЧИКИ ЭТАПОВ НАТЯЖНЫХ ПОТОЛКОВ ==========

@router.callback_query(F.data.startswith("profile:"))
async def process_profile_choice(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа профиля (Этап 2)"""
    profile_type = callback.data.split(":")[1]
    data = await state.get_data()
    perimeter = data.get('perimeter', 0)
    
    # Рассчитываем профиль
    profile_data = ceiling_calc.calculate_profile(perimeter)
    
    # Сохраняем данные
    await state.update_data(
        profile_type=profile_type,
        profile_data=profile_data
    )
    
    profile_name = settings.PROFILE_TYPES.get(profile_type, profile_type)
    
    # Переходим к выбору освещения
    await state.set_state(CalculationStates.choosing_lighting)
    await callback.message.edit_text(
        f"✅ Профиль выбран: {profile_name}\n\n"
        f"📐 Количество профиля: {profile_data['profile_quantity']:.2f} м\n"
        f"🔩 Дюбель-гвозди: {profile_data['dowel_nails_count']} шт\n\n"
        f"**Этап 3: Выбор освещения**\n\n"
        f"Выберите тип освещения:",
        reply_markup=get_lighting_type_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lighting:"))
async def process_lighting_choice(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа освещения (Этап 3)"""
    lighting_type = callback.data.split(":")[1]
    
    await state.update_data(lighting_type=lighting_type)
    lighting_name = settings.LIGHTING_TYPES.get(lighting_type, lighting_type)
    
    if lighting_type == "spot_lights":
        # Точечные светильники - выбираем диаметр
        await state.set_state(CalculationStates.spot_diameter_input)
        await callback.message.edit_text(
            f"✅ Освещение: {lighting_name}\n\n"
            f"**Выбор диаметра светильников**\n\n"
            f"Выберите диаметр точечных светильников:",
            reply_markup=get_spot_diameter_keyboard(),
            parse_mode="Markdown"
        )
    elif lighting_type == "light_lines":
        # Световые линии - выбираем ширину
        await state.set_state(CalculationStates.light_lines_width)
        await callback.message.edit_text(
            f"✅ Освещение: {lighting_name}\n\n"
            f"**Выбор ширины световых линий**\n\n"
            f"Выберите ширину световых линий:",
            reply_markup=get_light_line_width_keyboard(),
            parse_mode="Markdown"
        )
    elif lighting_type == "floating_light":
        # Парящая подсветка - вводим метры
        await state.set_state(CalculationStates.floating_light_meters)
        await callback.message.edit_text(
            f"✅ Освещение: {lighting_name}\n\n"
            f"**Ввод длины парящей подсветки**\n\n"
            f"Введите погонные метры парящей подсветки:",
            parse_mode="Markdown"
        )
    else:
        # Люстра, комбинированное или без освещения - переходим сразу к нишам
        lighting_data = {"type": lighting_type}
        await state.update_data(lighting_data=lighting_data)
        await move_to_curtain_niche_choice(callback, state)
    
    await callback.answer()


@router.callback_query(F.data.startswith("spot_diameter:"))
async def process_spot_diameter(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора диаметра точечных светильников"""
    diameter_data = callback.data.split(":")[1]
    
    if diameter_data == "custom":
        await state.set_state(CalculationStates.custom_diameter_input)
        await callback.message.edit_text(
            "📝 **Ввод диаметра**\n\n"
            "Введите диаметр светильника в миллиметрах (например: 75):",
            parse_mode="Markdown"
        )
    else:
        diameter = int(diameter_data)
        await state.update_data(spot_diameter=diameter)
        
        # Переходим к вводу количества
        await state.set_state(CalculationStates.spot_count_input)
        await callback.message.edit_text(
            f"✅ Диаметр: {diameter} мм\n\n"
            f"**Ввод количества светильников**\n\n"
            f"Введите количество точечных светильников:",
            parse_mode="Markdown"
        )
    
    await callback.answer()


@router.message(CalculationStates.custom_diameter_input)
async def process_custom_diameter(message: types.Message, state: FSMContext):
    """Обработка ввода кастомного диаметра"""
    try:
        diameter = int(message.text.strip())
        if diameter < 30 or diameter > 200:
            await message.answer(
                "❌ Диаметр должен быть от 30 до 200 мм.\nПопробуйте еще раз:"
            )
            return
        
        await state.update_data(spot_diameter=diameter)
        
        # Переходим к вводу количества
        await state.set_state(CalculationStates.spot_count_input)
        await message.answer(
            f"✅ Диаметр: {diameter} мм\n\n"
            f"**Ввод количества светильников**\n\n"
            f"Введите количество точечных светильников:",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer(
            "❌ Введите корректное число.\nПример: 65"
        )


@router.message(CalculationStates.spot_count_input)
async def process_spot_count(message: types.Message, state: FSMContext):
    """Обработка ввода количества точечных светильников"""
    try:
        count = int(message.text.strip())
        if count < 1 or count > 50:
            await message.answer(
                "❌ Количество должно быть от 1 до 50 штук.\nПопробуйте еще раз:"
            )
            return
        
        data = await state.get_data()
        diameter = data.get('spot_diameter')
        
        # Рассчитываем светильники
        lighting_data = ceiling_calc.calculate_spot_lights(count, diameter)
        lighting_data["type"] = "spot_lights"
        
        await state.update_data(lighting_data=lighting_data)
        
        # Переходим к нишам под шторы
        await move_to_curtain_niche_choice_text(message, state)
        
    except ValueError:
        await message.answer(
            "❌ Введите корректное число.\nПример: 6"
        )


@router.callback_query(F.data.startswith("light_width:"))
async def process_light_line_width(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора ширины световых линий"""
    width = int(callback.data.split(":")[1])
    await state.update_data(light_line_width=width)
    
    # Переходим к вводу метров
    await state.set_state(CalculationStates.light_lines_meters)
    await callback.message.edit_text(
        f"✅ Ширина световых линий: {width} см\n\n"
        f"**Ввод длины световых линий**\n\n"
        f"Введите погонные метры световых линий:",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(CalculationStates.light_lines_meters)
async def process_light_lines_meters(message: types.Message, state: FSMContext):
    """Обработка ввода метров световых линий"""
    try:
        meters = float(message.text.strip().replace(',', '.'))
        if meters <= 0 or meters > 100:
            await message.answer(
                "❌ Длина должна быть от 0.1 до 100 метров.\nПопробуйте еще раз:"
            )
            return
        
        await state.update_data(light_line_meters=meters)
        
        # Переходим к выбору углов
        await state.set_state(CalculationStates.light_lines_corners)
        await message.answer(
            f"✅ Длина световых линий: {meters} м\n\n"
            f"**Выбор количества углов 90°**\n\n"
            f"Выберите количество углов 90°:",
            reply_markup=get_corners_count_keyboard(),
            parse_mode="Markdown"
        )
        
    except ValueError:
        await message.answer(
            "❌ Введите корректное число.\nПример: 5.5"
        )


@router.callback_query(F.data.startswith("corners:"))
async def process_corners_count(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора количества углов"""
    corners_data = callback.data.split(":")[1]
    
    if corners_data == "more":
        await state.set_state(CalculationStates.custom_corners_input)
        await callback.message.edit_text(
            "📝 **Ввод количества углов**\n\n"
            "Введите количество углов 90° (например: 6):",
            parse_mode="Markdown"
        )
    else:
        corners = int(corners_data)
        await state.update_data(light_line_corners=corners)
        
        # Переходим к выбору перекрестий
        await state.set_state(CalculationStates.light_lines_crossings)
        await callback.message.edit_text(
            f"✅ Углы 90°: {corners} шт\n\n"
            f"**Выбор количества перекрестий**\n\n"
            f"Выберите количество перекрестий:",
            reply_markup=get_crossings_count_keyboard(),
            parse_mode="Markdown"
        )
    
    await callback.answer()


@router.message(CalculationStates.custom_corners_input)
async def process_custom_corners(message: types.Message, state: FSMContext):
    """Обработка ввода кастомного количества углов"""
    try:
        corners = int(message.text.strip())
        if corners < 0 or corners > 20:
            await message.answer(
                "❌ Количество углов должно быть от 0 до 20.\nПопробуйте еще раз:"
            )
            return
        
        await state.update_data(light_line_corners=corners)
        
        # Переходим к выбору перекрестий
        await state.set_state(CalculationStates.light_lines_crossings)
        await message.answer(
            f"✅ Углы 90°: {corners} шт\n\n"
            f"**Выбор количества перекрестий**\n\n"
            f"Выберите количество перекрестий:",
            reply_markup=get_crossings_count_keyboard(),
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer(
            "❌ Введите корректное число.\nПример: 5"
        )


@router.callback_query(F.data.startswith("crossings:"))
async def process_crossings_count(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора количества перекрестий"""
    crossings_data = callback.data.split(":")[1]
    
    if crossings_data == "more":
        await state.set_state(CalculationStates.custom_crossings_input)
        await callback.message.edit_text(
            "📝 **Ввод количества перекрестий**\n\n"
            "Введите количество перекрестий (например: 4):",
            parse_mode="Markdown"
        )
    else:
        crossings = int(crossings_data)
        await finish_light_lines_calculation(callback, state, crossings)
    
    await callback.answer()


@router.message(CalculationStates.custom_crossings_input)
async def process_custom_crossings(message: types.Message, state: FSMContext):
    """Обработка ввода кастомного количества перекрестий"""
    try:
        crossings = int(message.text.strip())
        if crossings < 0 or crossings > 20:
            await message.answer(
                "❌ Количество перекрестий должно быть от 0 до 20.\nПопробуйте еще раз:"
            )
            return
        
        await finish_light_lines_calculation_text(message, state, crossings)
        
    except ValueError:
        await message.answer(
            "❌ Введите корректное число.\nПример: 2"
        )


@router.message(CalculationStates.floating_light_meters)
async def process_floating_light_meters(message: types.Message, state: FSMContext):
    """Обработка ввода метров парящей подсветки"""
    try:
        meters = float(message.text.strip().replace(',', '.'))
        if meters <= 0 or meters > 100:
            await message.answer(
                "❌ Длина должна быть от 0.1 до 100 метров.\nПопробуйте еще раз:"
            )
            return
        
        # Рассчитываем парящую подсветку
        lighting_data = ceiling_calc.calculate_floating_light(meters)
        lighting_data["type"] = "floating_light"
        
        await state.update_data(lighting_data=lighting_data)
        
        # Переходим к нишам под шторы
        await move_to_curtain_niche_choice_text(message, state)
        
    except ValueError:
        await message.answer(
            "❌ Введите корректное число.\nПример: 8.5"
        )


@router.callback_query(F.data.startswith("curtain_niche:"))
async def process_curtain_niche_choice(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора ниши под шторы (Этап 4)"""
    choice = callback.data.split(":")[1]
    
    if choice == "yes":
        await state.set_state(CalculationStates.curtain_niche_type)
        await callback.message.edit_text(
            "✅ Ниши под шторы требуются\n\n"
            "**Этап 4: Выбор типа ниши**\n\n"
            "Выберите тип ниши под шторы:",
            reply_markup=get_curtain_niche_type_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await state.update_data(curtain_niche_needed=False)
        await move_to_timber_choice(callback, state)
    
    await callback.answer()


@router.callback_query(F.data.startswith("curtain_type:"))
async def process_curtain_niche_type(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа ниши под шторы"""
    niche_type = callback.data.split(":")[1]
    await state.update_data(curtain_niche_type=niche_type)
    
    niche_name = settings.CURTAIN_NICHE_TYPES.get(niche_type, niche_type)
    
    await state.set_state(CalculationStates.curtain_niche_meters)
    await callback.message.edit_text(
        f"✅ Тип ниши: {niche_name}\n\n"
        f"**Ввод метража ниши**\n\n"
        f"Введите погонные метры ниши под шторы:",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(CalculationStates.curtain_niche_meters)
async def process_curtain_niche_meters(message: types.Message, state: FSMContext):
    """Обработка ввода метров ниши под шторы"""
    try:
        meters = float(message.text.strip().replace(',', '.'))
        if meters <= 0 or meters > 50:
            await message.answer(
                "❌ Длина должна быть от 0.1 до 50 метров.\nПопробуйте еще раз:"
            )
            return
        
        data = await state.get_data()
        niche_type = data.get('curtain_niche_type')
        
        # Рассчитываем нишу
        if niche_type == "u_shaped":
            curtain_data = ceiling_calc.calculate_curtain_niche_u_shaped(meters)
        else:
            curtain_data = ceiling_calc.calculate_curtain_niche_l_shaped(meters)
        
        curtain_data["type"] = niche_type
        curtain_data["needed"] = True
        
        await state.update_data(
            curtain_niche_needed=True,
            curtain_data=curtain_data
        )
        
        # Переходим к выбору бруса
        await move_to_timber_choice_text(message, state)
        
    except ValueError:
        await message.answer(
            "❌ Введите корректное число.\nПример: 3.2"
        )


@router.callback_query(F.data.startswith("timber:"))
async def process_timber_choice(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора бруса (Этап 5)"""
    choice = callback.data.split(":")[1]
    
    if choice == "yes":
        await state.set_state(CalculationStates.timber_meters)
        await callback.message.edit_text(
            "✅ Брус требуется\n\n"
            "**Этап 5: Ввод метража бруса**\n\n"
            "Введите погонные метры бруса:",
            parse_mode="Markdown"
        )
    else:
        await state.update_data(timber_needed=False)
        await move_to_fastener_choice(callback, state)
    
    await callback.answer()


@router.message(CalculationStates.timber_meters)
async def process_timber_meters(message: types.Message, state: FSMContext):
    """Обработка ввода метров бруса"""
    try:
        meters = float(message.text.strip().replace(',', '.'))
        if meters <= 0 or meters > 100:
            await message.answer(
                "❌ Длина должна быть от 0.1 до 100 метров.\nПопробуйте еще раз:"
            )
            return
        
        # Рассчитываем брус
        timber_data = ceiling_calc.calculate_timber(meters)
        timber_data["needed"] = True
        
        await state.update_data(
            timber_needed=True,
            timber_data=timber_data
        )
        
        # Переходим к выбору крепежа
        await move_to_fastener_choice_text(message, state)
        
    except ValueError:
        await message.answer(
            "❌ Введите корректное число.\nПример: 12.5"
        )


@router.callback_query(F.data.startswith("fastener:"))
async def process_fastener_choice(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора крепежа (Этап 6)"""
    fastener_type = callback.data.split(":")[1]
    await state.update_data(fastener_type=fastener_type)
    
    # Выполняем финальные расчеты и формируем смету
    await finalize_ceiling_calculation(callback, state)
    await callback.answer()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def finish_light_lines_calculation(callback: types.CallbackQuery, state: FSMContext, crossings: int):
    """Завершение расчета световых линий"""
    data = await state.get_data()
    meters = data.get('light_line_meters')
    corners = data.get('light_line_corners')
    
    # Рассчитываем световые линии
    lighting_data = ceiling_calc.calculate_light_lines(meters, corners, crossings)
    lighting_data["type"] = "light_lines"
    
    await state.update_data(lighting_data=lighting_data)
    
    # Переходим к нишам под шторы
    await move_to_curtain_niche_choice(callback, state)


async def finish_light_lines_calculation_text(message: types.Message, state: FSMContext, crossings: int):
    """Завершение расчета световых линий (для текстового сообщения)"""
    data = await state.get_data()
    meters = data.get('light_line_meters')
    corners = data.get('light_line_corners')
    
    # Рассчитываем световые линии
    lighting_data = ceiling_calc.calculate_light_lines(meters, corners, crossings)
    lighting_data["type"] = "light_lines"
    
    await state.update_data(lighting_data=lighting_data)
    
    # Переходим к нишам под шторы
    await move_to_curtain_niche_choice_text(message, state)


async def move_to_curtain_niche_choice(callback: types.CallbackQuery, state: FSMContext):
    """Переход к выбору ниши под шторы"""
    await state.set_state(CalculationStates.curtain_niche_choice)
    await callback.message.edit_text(
        "**Этап 4: Ниши под шторы**\n\n"
        "Нужны ли ниши под шторы?",
        reply_markup=get_yes_no_keyboard("curtain_niche"),
        parse_mode="Markdown"
    )


async def move_to_curtain_niche_choice_text(message: types.Message, state: FSMContext):
    """Переход к выбору ниши под шторы (для текстового сообщения)"""
    await state.set_state(CalculationStates.curtain_niche_choice)
    await message.answer(
        "**Этап 4: Ниши под шторы**\n\n"
        "Нужны ли ниши под шторы?",
        reply_markup=get_yes_no_keyboard("curtain_niche"),
        parse_mode="Markdown"
    )


async def move_to_timber_choice(callback: types.CallbackQuery, state: FSMContext):
    """Переход к выбору бруса"""
    await state.set_state(CalculationStates.timber_choice)
    await callback.message.edit_text(
        "**Этап 5: Дополнительные элементы**\n\n"
        "Требуется ли установка бруса?",
        reply_markup=get_yes_no_keyboard("timber"),
        parse_mode="Markdown"
    )


async def move_to_timber_choice_text(message: types.Message, state: FSMContext):
    """Переход к выбору бруса (для текстового сообщения)"""
    await state.set_state(CalculationStates.timber_choice)
    await message.answer(
        "**Этап 5: Дополнительные элементы**\n\n"
        "Требуется ли установка бруса?",
        reply_markup=get_yes_no_keyboard("timber"),
        parse_mode="Markdown"
    )


async def move_to_fastener_choice(callback: types.CallbackQuery, state: FSMContext):
    """Переход к выбору крепежа"""
    await state.set_state(CalculationStates.fastener_choice)
    await callback.message.edit_text(
        "**Этап 6: Выбор крепежа**\n\n"
        "Выберите тип основного крепежа:",
        reply_markup=get_fastener_type_keyboard(),
        parse_mode="Markdown"
    )


async def move_to_fastener_choice_text(message: types.Message, state: FSMContext):
    """Переход к выбору крепежа (для текстового сообщения)"""
    await state.set_state(CalculationStates.fastener_choice)
    await message.answer(
        "**Этап 6: Выбор крепежа**\n\n"
        "Выберите тип основного крепежа:",
        reply_markup=get_fastener_type_keyboard(),
        parse_mode="Markdown"
    )


async def finalize_ceiling_calculation(callback: types.CallbackQuery, state: FSMContext):
    """Финальные расчеты и формирование сметы"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    # Получаем все данные
    perimeter = data.get('perimeter', 0)
    area = data.get('area', 0)
    corners_count = data.get('corners_count', 4)
    measurements = data.get('measurements', [])
    room_type = data.get('room_type', 'rectangle')
    
    profile_type = data.get('profile_type')
    profile_data = data.get('profile_data', {})
    
    lighting_type = data.get('lighting_type')
    lighting_data = data.get('lighting_data', {})
    
    curtain_data = data.get('curtain_data')
    timber_data = data.get('timber_data')
    fastener_type = data.get('fastener_type')
    
    # Рассчитываем итоговые материалы
    totals = ceiling_calc.calculate_totals(
        area=area,
        perimeter=perimeter,
        lighting_data=lighting_data,
        curtain_data=curtain_data,
        floating_data=lighting_data if lighting_type == "floating_light" else None,
        timber_data=timber_data,
        profile_data=profile_data
    )
    
    # Формируем смету
    estimate_text = ceiling_calc.format_estimate(
        perimeter=perimeter,
        area=area,
        corners_count=corners_count,
        profile_type=profile_type,
        profile_data=profile_data,
        lighting_type=lighting_type,
        lighting_data=lighting_data,
        curtain_data=curtain_data,
        timber_data=timber_data,
        fastener_type=fastener_type,
        totals=totals
    )
    
    # Сохраняем расчет в базу данных
    await db.save_calculation(
        user_id=user_id,
        calculation_type="ceiling",
        room_type=room_type,
        room_description="Натяжной потолок",
        measurements=measurements,
        perimeter=perimeter,
        area=area,
        corners_count=corners_count,
        profile_type=profile_type,
        profile_quantity=profile_data.get('profile_quantity'),
        dowel_nails_count=profile_data.get('dowel_nails_count'),
        lighting_type=lighting_type,
        lighting_data=lighting_data,
        curtain_niche_needed=data.get('curtain_niche_needed', False),
        curtain_niche_type=curtain_data.get('type') if curtain_data else None,
        curtain_niche_meters=curtain_data.get('meters') if curtain_data else None,
        curtain_ends_count=curtain_data.get('ends_count') if curtain_data else None,
        curtain_tape_meters=curtain_data.get('tape_meters') if curtain_data else None,
        curtain_brackets_count=curtain_data.get('brackets_count') if curtain_data else None,
        curtain_screws_count=curtain_data.get('screws_count') if curtain_data else None,
        timber_needed=data.get('timber_needed', False),
        timber_meters=timber_data.get('meters') if timber_data else None,
        timber_brackets_count=timber_data.get('brackets_count') if timber_data else None,
        fastener_type=fastener_type,
        total_hangers=totals.get('total_hangers'),
        total_dowels=totals.get('total_dowels'),
        total_screws=totals.get('total_screws'),
        glue_volume=totals.get('glue_volume')
    )
    
    # Увеличиваем счетчик использований
    await db.increment_user_calculations(user_id)
    
    # Отправляем смету
    await callback.message.edit_text(
        estimate_text,
        reply_markup=get_estimate_keyboard(),
        parse_mode="Markdown"
    )
    
    # Очищаем состояние
    await state.clear()


@router.callback_query(F.data.startswith("estimate:"))
async def process_estimate_action(callback: types.CallbackQuery, state: FSMContext):
    """Обработка действий со сметой"""
    action = callback.data.split(":")[1]
    
    if action == "new":
        # Новый расчет
        await state.clear()
        await callback.message.edit_text(
            "Выберите тип расчета:",
            reply_markup=get_calculation_type_keyboard()
        )
        await state.set_state(CalculationStates.choosing_type)
    elif action == "edit":
        # Редактирование (пока заглушка)
        await callback.answer("🚧 Функция редактирования в разработке")
    elif action in ["pdf", "excel"]:
        # Экспорт (пока заглушка)
        await callback.answer("🚧 Функция экспорта в разработке")
    
    await callback.answer() 