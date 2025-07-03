import google.generativeai as genai
import json
from typing import Dict, Any, Optional, List
from PIL import Image
import io
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Настройка Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiRecognizer:
    def __init__(self):
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.recognition_prompt = """
        Проанализируй изображение с замерами помещений для натяжных потолков.
        
        Твоя задача:
        1. Найти ВСЕ чертежи/схемы помещений на изображении
        2. Для каждого помещения найти все числовые размеры в сантиметрах (см), метрах (м) или миллиметрах (мм)
        3. Определить форму каждого помещения (прямоугольник или сложная форма)
        4. Идентифицировать какой размер к какой стороне относится
        5. Если единицы измерения не указаны, считать что это сантиметры
        6. Все размеры конвертировать в сантиметры для единообразия
        7. Пронумеровать помещения в порядке их расположения на листе (слева направо, сверху вниз)
        
        ВАЖНО: Найди ВСЕ помещения на листе, даже если их много!
        
        Верни результат ТОЛЬКО в JSON формате без дополнительного текста:
        {
            "rooms": [
                {
                    "room_number": 1,
                    "room_type": "rectangle",
                    "measurements": [
                        {"side": "length", "value": 350, "unit": "cm", "original_text": "350"},
                        {"side": "width", "value": 280, "unit": "cm", "original_text": "280"}
                    ],
                    "position": "верхний левый угол",
                    "confidence": 0.95
                },
                {
                    "room_number": 2,
                    "room_type": "complex",
                    "measurements": [
                        {"side": "side1", "value": 300, "unit": "cm", "original_text": "30"},
                        {"side": "side2", "value": 250, "unit": "cm", "original_text": "25"},
                        {"side": "side3", "value": 150, "unit": "cm", "original_text": "15"}
                    ],
                    "position": "верхний правый угол",
                    "confidence": 0.90
                }
            ],
            "total_rooms_found": 2,
            "notes": "Дополнительные заметки если есть"
        }
        
        Для прямоугольных помещений используй обозначения:
        - length - длина (больший размер)
        - width - ширина (меньший размер)
        
        Для сложных форм используй:
        - side1, side2, side3 и т.д. по порядку обхода контура
        
        Обязательно укажи позицию каждого помещения на листе для идентификации.
        """
    
    async def recognize_measurements(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """Распознает размеры всех помещений на изображении"""
        try:
            # Открываем изображение
            image = Image.open(io.BytesIO(image_data))
            
            # Отправляем запрос к Gemini
            response = self.model.generate_content([self.recognition_prompt, image])
            
            # Извлекаем JSON из ответа
            response_text = response.text.strip()
            
            # Пытаемся найти JSON в ответе
            if response_text.startswith('{') and response_text.endswith('}'):
                result = json.loads(response_text)
            else:
                # Если ответ содержит текст помимо JSON, пытаемся извлечь JSON
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    logger.error(f"Не удалось извлечь JSON из ответа: {response_text}")
                    return None
            
            # Конвертируем все размеры в сантиметры для всех помещений
            for room in result.get('rooms', []):
                for measurement in room.get('measurements', []):
                    value = measurement['value']
                    unit = measurement.get('unit', 'cm')
                    
                    if unit == 'm':
                        measurement['value'] = value * 100
                        measurement['unit'] = 'cm'
                    elif unit == 'mm':
                        measurement['value'] = value / 10
                        measurement['unit'] = 'cm'
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка распознавания: {e}")
            return None
    
    async def validate_recognition(self, recognition_data: Dict[str, Any]) -> bool:
        """Проверяет корректность распознанных данных"""
        if not recognition_data:
            return False
        
        # Проверяем наличие обязательных полей
        if 'rooms' not in recognition_data:
            return False
        
        rooms = recognition_data.get('rooms', [])
        if not rooms:
            return False
        
        # Проверяем каждое помещение
        for room in rooms:
            # Проверяем обязательные поля помещения
            required_fields = ['room_type', 'measurements', 'room_number']
            for field in required_fields:
                if field not in room:
                    return False
            
            # Проверяем, что есть хотя бы 2 размера для прямоугольника
            measurements = room.get('measurements', [])
            if room['room_type'] == 'rectangle' and len(measurements) < 2:
                return False
            
            # Проверяем, что все размеры положительные
            for measurement in measurements:
                if measurement.get('value', 0) <= 0:
                    return False
        
        return True
    
    def format_measurements_text(self, recognition_data: Dict[str, Any]) -> str:
        """Форматирует распознанные размеры всех помещений в читаемый текст"""
        if not recognition_data:
            return "Размеры не распознаны"
        
        rooms = recognition_data.get('rooms', [])
        total_rooms = recognition_data.get('total_rooms_found', len(rooms))
        
        if not rooms:
            return "Помещения не найдены"
        
        text = f"🏠 Найдено помещений: {total_rooms}\n\n"
        
        for room in rooms:
            room_number = room.get('room_number', '?')
            room_type = room.get('room_type', 'unknown')
            measurements = room.get('measurements', [])
            confidence = room.get('confidence', 0)
            position = room.get('position', 'неизвестно')
            
            text += f"📍 **Помещение #{room_number}** ({position})\n"
            text += f"🏠 Тип: {'Прямоугольник' if room_type == 'rectangle' else 'Сложная форма'}\n"
            text += f"📏 Размеры:\n"
            
            for measurement in measurements:
                side = measurement.get('side', 'сторона')
                value = measurement.get('value', 0)
                original = measurement.get('original_text', '')
                
                if room_type == 'rectangle':
                    if side == 'length':
                        side_text = 'Длина'
                    elif side == 'width':
                        side_text = 'Ширина'
                    else:
                        side_text = side
                else:
                    side_text = f"Сторона {side.replace('side', '')}"
                
                text += f"  • {side_text}: {value} см"
                if original:
                    text += f" (распознано: {original})"
                text += "\n"
            
            if confidence:
                text += f"🎯 Уверенность: {int(confidence * 100)}%\n"
            
            text += "\n"
        
        return text


# Создаем экземпляр распознавателя
recognizer = GeminiRecognizer() 