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
    get_main_keyboard
)
from bot.database.models import db
from bot.utils.gemini_api import recognizer
from bot.utils.calculator import calculator
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
        "complete": "🎯 Комплексный расчет"
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
        
        # Выполняем расчеты для всех помещений
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