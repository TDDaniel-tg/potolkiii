from typing import Dict, Any, List, Tuple
import math
from config.settings import settings


class CeilingCalculator:
    """Калькулятор для расчета натяжных потолков"""
    
    def calculate_multiple_rooms(self, recognition_data: Dict[str, Any], calculation_type: str, fabric_width: int = None) -> List[Dict[str, Any]]:
        """
        Рассчитывает размеры для всех помещений
        
        Args:
            recognition_data: Данные распознавания с несколькими помещениями
            calculation_type: Тип расчета (perimeter/area/fabric/both/complete)
            fabric_width: Ширина ткани для расчета
        
        Returns:
            Список результатов для каждого помещения
        """
        results = []
        rooms = recognition_data.get('rooms', [])
        
        for room in rooms:
            room_data = {
                'room_type': room.get('room_type'),
                'measurements': room.get('measurements', [])
            }
            
            # Рассчитываем для текущего помещения
            result = self.format_calculation_result(
                calculation_type=calculation_type,
                recognition_data=room_data
            )
            
            # Добавляем информацию о помещении
            result['room_number'] = room.get('room_number')
            result['position'] = room.get('position', 'неизвестно')
            result['confidence'] = room.get('confidence', 0)
            
            # Выполняем расчеты
            measurements = room.get('measurements', [])
            room_type = room.get('room_type')
            
            if calculation_type in ['perimeter', 'both', 'complete']:
                perimeter = self.calculate_perimeter(measurements, room_type)
                result['perimeter'] = {
                    'value_cm': round(perimeter, 2),
                    'value_m': round(perimeter / 100, 2),
                    'margin_percent': settings.DEFAULT_PERIMETER_MARGIN
                }
            
            if calculation_type in ['area', 'both', 'complete']:
                area = self.calculate_area(measurements, room_type)
                result['area'] = {
                    'value_cm2': round(area, 2),
                    'value_m2': round(area / 10000, 2),
                    'margin_percent': settings.DEFAULT_AREA_MARGIN
                }
            
            if calculation_type in ['fabric', 'complete']:
                fabric_data = self.calculate_fabric_requirements(measurements, room_type, fabric_width)
                result['fabric'] = fabric_data
            
            results.append(result)
        
        return results
    
    def format_multiple_results_text(self, results: List[Dict[str, Any]], calculation_type: str) -> str:
        """Форматирует результаты расчета для всех помещений"""
        if not results:
            return "Нет результатов для отображения"
        
        text = "📊 **РЕЗУЛЬТАТЫ РАСЧЕТА**\n\n"
        
        # Тип расчета
        type_descriptions = {
            'perimeter': '📐 Расчет периметра (для плинтуса/багета)',
            'area': '📏 Расчет площади (для полотна потолка)',
            'fabric': '🧵 Расчет ткани (количество метров)',
            'both': '📐📏 Полный расчет (периметр + площадь)',
            'complete': '🎯 Комплексный расчет (все параметры)'
        }
        
        text += f"{type_descriptions.get(calculation_type, 'Расчет')}\n"
        text += f"🏠 Обработано помещений: {len(results)}\n\n"
        
        # Результаты для каждого помещения
        total_perimeter = 0
        total_area = 0
        total_fabric = 0
        
        for i, result in enumerate(results):
            room_number = result.get('room_number', i + 1)
            position = result.get('position', 'неизвестно')
            confidence = result.get('confidence', 0)
            room_type = result.get('room_type', 'unknown')
            
            text += f"{'='*30}\n"
            text += f"📍 **ПОМЕЩЕНИЕ #{room_number}**\n"
            text += f"🗺️ Позиция: {position}\n"
            text += f"🏠 Тип: {'Прямоугольник' if room_type == 'rectangle' else 'Сложная форма'}\n"
            
            if confidence:
                text += f"🎯 Уверенность: {int(confidence * 100)}%\n"
            
            text += "\n"
            
            # Размеры
            measurements = result.get('measurements', [])
            if measurements:
                text += "📏 **Размеры:**\n"
                for measurement in measurements:
                    side = measurement.get('side', 'сторона')
                    value = measurement.get('value', 0)
                    
                    if room_type == 'rectangle':
                        if side == 'length':
                            side_text = 'Длина'
                        elif side == 'width':
                            side_text = 'Ширина'
                        else:
                            side_text = side
                    else:
                        side_text = f"Сторона {side.replace('side', '')}"
                    
                    text += f"  • {side_text}: {value} см\n"
                text += "\n"
            
            # Периметр
            if 'perimeter' in result:
                perimeter_data = result['perimeter']
                text += "📐 **ПЕРИМЕТР:**\n"
                text += f"• С припуском: {perimeter_data['value_m']:.2f} м\n"
                
                margin = perimeter_data['margin_percent']
                if margin > 0:
                    clean_perimeter = perimeter_data['value_cm'] / (1 + margin / 100)
                    text += f"• Без припуска: {clean_perimeter / 100:.2f} м\n"
                    text += f"• Припуск: {margin}%\n"
                text += "\n"
                
                total_perimeter += perimeter_data['value_m']
            
            # Площадь
            if 'area' in result:
                area_data = result['area']
                text += "📏 **ПЛОЩАДЬ:**\n"
                text += f"• С припуском: {area_data['value_m2']:.2f} м²\n"
                
                margin = area_data['margin_percent']
                if margin > 0:
                    clean_area = area_data['value_cm2'] / (1 + margin / 100)
                    text += f"• Без припуска: {clean_area / 10000:.2f} м²\n"
                    text += f"• Припуск: {margin}%\n"
                text += "\n"
                
                total_area += area_data['value_m2']
            
            # Ткань
            if 'fabric' in result:
                fabric_text = self.format_fabric_calculation_text(result['fabric'])
                text += fabric_text
                
                total_fabric += result['fabric']['total_length_m']
        
        # Итоговые суммы
        if len(results) > 1:
            text += f"{'='*30}\n"
            text += "📊 **ИТОГО ПО ВСЕМ ПОМЕЩЕНИЯМ:**\n\n"
            
            if total_perimeter > 0:
                text += f"📐 Общий периметр: **{total_perimeter:.2f} м**\n"
                text += f"💰 Плинтус/багет: ~{total_perimeter:.1f} м\n\n"
            
            if total_area > 0:
                text += f"📏 Общая площадь: **{total_area:.2f} м²**\n"
                text += f"💰 Полотно потолка: ~{total_area:.1f} м²\n\n"
            
            if total_fabric > 0:
                text += f"🧵 Общий расход ткани: **{total_fabric:.2f} м**\n"
                text += f"💰 Ткань к заказу: ~{total_fabric + len(results) * 0.5:.1f} м\n\n"
            
            text += "💡 **Рекомендации по закупке:**\n"
            if total_perimeter > 0:
                text += f"• Плинтус/багет: {total_perimeter * 1.05:.1f} м (с запасом 5%)\n"
            if total_area > 0:
                text += f"• Полотно: {total_area * 1.02:.1f} м² (с запасом 2%)\n"
            if total_fabric > 0:
                text += f"• Ткань: {total_fabric + len(results) * 0.5:.1f} м (с запасом по помещениям)\n"
        
        return text
    
    def calculate_perimeter(self, measurements: List[Dict[str, Any]], 
                          room_type: str, 
                          margin_percent: int = None) -> float:
        """
        Рассчитывает периметр помещения с учетом припуска
        
        Args:
            measurements: Список измерений
            room_type: Тип помещения (rectangle/complex)
            margin_percent: Процент припуска (по умолчанию из настроек)
        
        Returns:
            Периметр в сантиметрах с учетом припуска
        """
        if margin_percent is None:
            margin_percent = settings.DEFAULT_PERIMETER_MARGIN
        
        if room_type == "rectangle":
            # Для прямоугольника: P = 2 * (длина + ширина)
            length = 0
            width = 0
            
            for measurement in measurements:
                if measurement.get('side') == 'length':
                    length = measurement.get('value', 0)
                elif measurement.get('side') == 'width':
                    width = measurement.get('value', 0)
            
            perimeter = 2 * (length + width)
        else:
            # Для сложной формы: сумма всех сторон
            perimeter = sum(m.get('value', 0) for m in measurements)
        
        # Добавляем припуск
        return perimeter * (1 + margin_percent / 100)
    
    def calculate_area(self, measurements: List[Dict[str, Any]], 
                      room_type: str, 
                      margin_percent: int = None) -> float:
        """
        Рассчитывает площадь помещения с учетом припуска
        
        Args:
            measurements: Список измерений
            room_type: Тип помещения (rectangle/complex)
            margin_percent: Процент припуска (по умолчанию из настроек)
        
        Returns:
            Площадь в квадратных сантиметрах с учетом припуска
        """
        if margin_percent is None:
            margin_percent = settings.DEFAULT_AREA_MARGIN
        
        if room_type == "rectangle":
            # Для прямоугольника: S = длина * ширина
            length = 0
            width = 0
            
            for measurement in measurements:
                if measurement.get('side') == 'length':
                    length = measurement.get('value', 0)
                elif measurement.get('side') == 'width':
                    width = measurement.get('value', 0)
            
            area = length * width
        else:
            # Для сложной формы используем приближенный расчет
            # Предполагаем, что пользователь ввел размеры по порядку обхода
            area = self._calculate_polygon_area(measurements)
        
        # Добавляем припуск
        return area * (1 + margin_percent / 100)
    
    def _calculate_polygon_area(self, measurements: List[Dict[str, Any]]) -> float:
        """
        Приближенный расчет площади многоугольника
        Для упрощения считаем как прямоугольник с максимальными размерами
        """
        if len(measurements) < 3:
            return 0
        
        # Берем два максимальных размера как приближение
        values = sorted([m.get('value', 0) for m in measurements], reverse=True)
        if len(values) >= 2:
            return values[0] * values[1]
        return 0
    
    def format_calculation_result(self, 
                                calculation_type: str,
                                recognition_data: Dict[str, Any],
                                perimeter: float = None,
                                area: float = None,
                                perimeter_margin: int = None,
                                area_margin: int = None) -> Dict[str, Any]:
        """
        Форматирует результат расчета
        
        Returns:
            Словарь с результатами расчета
        """
        result = {
            'calculation_type': calculation_type,
            'room_type': recognition_data.get('room_type'),
            'measurements': recognition_data.get('measurements', [])
        }
        
        if perimeter is not None:
            result['perimeter'] = {
                'value_cm': round(perimeter, 2),
                'value_m': round(perimeter / 100, 2),
                'margin_percent': perimeter_margin or settings.DEFAULT_PERIMETER_MARGIN
            }
        
        if area is not None:
            result['area'] = {
                'value_cm2': round(area, 2),
                'value_m2': round(area / 10000, 2),
                'margin_percent': area_margin or settings.DEFAULT_AREA_MARGIN
            }
        
        return result
    
    def format_result_text(self, result: Dict[str, Any]) -> str:
        """Форматирует результат расчета в читаемый текст"""
        text = "📊 **РЕЗУЛЬТАТ РАСЧЕТА**\n\n"
        
        # Тип расчета
        calc_type = result.get('calculation_type', '')
        if calc_type == 'perimeter':
            text += "📐 Расчет периметра (для плинтуса/багета)\n"
        elif calc_type == 'area':
            text += "📏 Расчет площади (для полотна потолка)\n"
        elif calc_type == 'both':
            text += "📐📏 Полный расчет (периметр + площадь)\n"
        
        text += "\n"
        
        # Периметр
        if 'perimeter' in result:
            perimeter_data = result['perimeter']
            text += "**ПЕРИМЕТР:**\n"
            text += f"• Чистый размер: {perimeter_data['value_m']:.2f} м "
            text += f"({perimeter_data['value_cm']:.0f} см)\n"
            
            margin = perimeter_data['margin_percent']
            if margin > 0:
                clean_perimeter = perimeter_data['value_cm'] / (1 + margin / 100)
                text += f"• Без припуска: {clean_perimeter / 100:.2f} м\n"
                text += f"• Припуск: {margin}%\n"
            text += "\n"
        
        # Площадь
        if 'area' in result:
            area_data = result['area']
            text += "**ПЛОЩАДЬ:**\n"
            text += f"• Чистый размер: {area_data['value_m2']:.2f} м² "
            text += f"({area_data['value_cm2']:.0f} см²)\n"
            
            margin = area_data['margin_percent']
            if margin > 0:
                clean_area = area_data['value_cm2'] / (1 + margin / 100)
                text += f"• Без припуска: {clean_area / 10000:.2f} м²\n"
                text += f"• Припуск: {margin}%\n"
            text += "\n"
        
        # Рекомендации
        text += "💡 **Рекомендации:**\n"
        if 'perimeter' in result:
            text += f"• Закупите плинтус/багет: {result['perimeter']['value_m']:.1f} м\n"
        if 'area' in result:
            text += f"• Закупите полотно: {result['area']['value_m2']:.1f} м²\n"
        
        return text
    
    def parse_manual_input(self, text: str, calculation_type: str) -> Dict[str, Any]:
        """
        Парсит ручной ввод размеров от пользователя
        
        Args:
            text: Текст с размерами
            calculation_type: Тип расчета
        
        Returns:
            Данные в формате recognition_data (для одного помещения)
        """
        # Извлекаем числа из текста
        import re
        numbers = re.findall(r'(\d+(?:\.\d+)?)\s*(?:см|м|мм)?', text)
        
        if not numbers:
            return None
        
        measurements = []
        
        # Конвертируем строки в числа
        values = [float(n) for n in numbers]
        
        # Определяем тип помещения
        if len(values) == 2:
            # Прямоугольник
            length = max(values)
            width = min(values)
            measurements = [
                {"side": "length", "value": length * 100 if length < 100 else length, "unit": "cm"},
                {"side": "width", "value": width * 100 if width < 100 else width, "unit": "cm"}
            ]
            room_type = "rectangle"
        else:
            # Сложная форма
            for i, value in enumerate(values):
                # Если значение меньше 100, считаем что это метры
                if value < 100:
                    value = value * 100
                measurements.append({
                    "side": f"side{i+1}", 
                    "value": value, 
                    "unit": "cm"
                })
            room_type = "complex"
        
        # Возвращаем в новом формате с массивом rooms
        return {
            "rooms": [{
                "room_number": 1,
                "room_type": room_type,
                "measurements": measurements,
                "position": "ручной ввод",
                "confidence": 1.0
            }],
            "total_rooms_found": 1,
            "notes": "Ручной ввод"
        }
    
    def calculate_fabric_requirements(self, measurements: List[Dict[str, Any]], 
                                     room_type: str, 
                                     fabric_width: int = None) -> Dict[str, Any]:
        """
        Рассчитывает требуемое количество ткани
        
        Args:
            measurements: Список измерений
            room_type: Тип помещения
            fabric_width: Ширина рулона в см (по умолчанию из настроек)
        
        Returns:
            Словарь с расчетом ткани
        """
        if fabric_width is None:
            fabric_width = settings.DEFAULT_FABRIC_WIDTH
        
        if room_type == "rectangle":
            return self._calculate_rectangle_fabric(measurements, fabric_width)
        else:
            return self._calculate_complex_fabric(measurements, fabric_width)
    
    def _calculate_rectangle_fabric(self, measurements: List[Dict[str, Any]], 
                                   fabric_width: int) -> Dict[str, Any]:
        """Расчет ткани для прямоугольного помещения"""
        length = 0
        width = 0
        
        for measurement in measurements:
            if measurement.get('side') == 'length':
                length = measurement.get('value', 0)
            elif measurement.get('side') == 'width':
                width = measurement.get('value', 0)
        
        # Варианты раскроя
        option1 = self._calculate_fabric_option(length, width, fabric_width)  # Длина вдоль рулона
        option2 = self._calculate_fabric_option(width, length, fabric_width)  # Ширина вдоль рулона
        
        # Выбираем оптимальный вариант (меньше расход)
        if option1['total_length'] <= option2['total_length']:
            optimal = option1
            optimal['direction'] = 'длина вдоль рулона'
        else:
            optimal = option2  
            optimal['direction'] = 'ширина вдоль рулона'
        
        optimal['room_length'] = length
        optimal['room_width'] = width
        optimal['fabric_width'] = fabric_width
        
        return optimal
    
    def _calculate_complex_fabric(self, measurements: List[Dict[str, Any]], 
                                 fabric_width: int) -> Dict[str, Any]:
        """Расчет ткани для помещения сложной формы"""
        values = [m.get('value', 0) for m in measurements]
        max_length = max(values) if values else 0
        second_max = sorted(values, reverse=True)[1] if len(values) > 1 else max_length
        
        # Используем два максимальных размера как приближение прямоугольника
        option1 = self._calculate_fabric_option(max_length, second_max, fabric_width)
        option2 = self._calculate_fabric_option(second_max, max_length, fabric_width)
        
        if option1['total_length'] <= option2['total_length']:
            optimal = option1
            optimal['direction'] = 'по максимальной стороне'
        else:
            optimal = option2
            optimal['direction'] = 'по второй стороне'
        
        optimal['room_length'] = max_length
        optimal['room_width'] = second_max
        optimal['fabric_width'] = fabric_width
        optimal['note'] = 'Приближенный расчет для сложной формы'
        
        return optimal
    
    def _calculate_fabric_option(self, room_length: float, room_width: float, 
                                fabric_width: int) -> Dict[str, Any]:
        """Рассчитывает один вариант раскроя"""
        
        # Добавляем припуски по краям
        length_with_allowance = room_length + (settings.FABRIC_EDGE_ALLOWANCE * 2)
        width_with_allowance = room_width + (settings.FABRIC_EDGE_ALLOWANCE * 2)
        
        if fabric_width >= width_with_allowance:
            # Можно кроить цельным куском
            strips_count = 1
            total_length = length_with_allowance
            seam_allowance = 0
            
        else:
            # Нужно несколько полос
            strips_count = math.ceil(width_with_allowance / fabric_width)
            
            # Учитываем припуски на швы
            seam_allowance = (strips_count - 1) * settings.FABRIC_SEAM_ALLOWANCE
            total_length = (length_with_allowance * strips_count) + seam_allowance
        
        return {
            'strips_count': strips_count,
            'strip_length': length_with_allowance,
            'total_length': total_length,
            'total_length_m': round(total_length / 100, 2),
            'seam_allowance': seam_allowance,
            'edge_allowance': settings.FABRIC_EDGE_ALLOWANCE * 2,
            'waste_percent': round(((total_length - (room_length * room_width / (fabric_width / 100))) / total_length) * 100, 1)
        }
    
    def format_fabric_calculation_text(self, fabric_data: Dict[str, Any]) -> str:
        """Форматирует результат расчета ткани"""
        if not fabric_data:
            return ""
        
        text = "\n🧵 **РАСЧЕТ ТКАНИ:**\n"
        text += f"📏 Ширина рулона: {fabric_data['fabric_width']} см\n"
        text += f"🔄 Направление: {fabric_data.get('direction', 'не указано')}\n\n"
        
        text += f"📊 **Детали раскроя:**\n"
        text += f"• Количество полос: {fabric_data['strips_count']}\n"
        text += f"• Длина полосы: {fabric_data['strip_length']:.0f} см\n"
        
        if fabric_data['seam_allowance'] > 0:
            text += f"• Припуск на швы: {fabric_data['seam_allowance']} см\n"
        
        text += f"• Припуск по краям: {fabric_data['edge_allowance']} см\n"
        text += f"• Отходы: ~{fabric_data['waste_percent']}%\n\n"
        
        text += f"🎯 **ИТОГО ТКАНИ: {fabric_data['total_length_m']} м**\n"
        text += f"💡 Рекомендуем заказать: {fabric_data['total_length_m'] + 0.5:.1f} м (с запасом)\n"
        
        if fabric_data.get('note'):
            text += f"\n📝 {fabric_data['note']}\n"
        
        return text


# Создаем экземпляр калькулятора
calculator = CeilingCalculator() 