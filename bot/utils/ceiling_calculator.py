from typing import Dict, Any, List, Tuple, Optional
import math
from config.settings import settings


class CeilingMaterialsCalculator:
    """Калькулятор материалов для натяжных потолков"""
    
    def __init__(self):
        self.coeffs = settings.CALCULATION_COEFFICIENTS
    
    def calculate_profile(self, perimeter: float) -> Dict[str, Any]:
        """
        Расчет профиля (Этап 2)
        
        Args:
            perimeter: Периметр помещения в метрах
            
        Returns:
            Dict с данными о профиле
        """
        # Количество профиля с запасом 5%
        profile_quantity = perimeter * (1 + self.coeffs["profile_margin"])
        
        # Количество дюбель-гвоздей (1 каждые 30 см)
        dowel_nails_count = math.ceil(perimeter * self.coeffs["dowel_nails_per_meter"])
        
        return {
            "profile_quantity": round(profile_quantity, 2),
            "dowel_nails_count": dowel_nails_count,
            "margin_percent": self.coeffs["profile_margin"] * 100
        }
    
    def calculate_spot_lights(self, count: int, diameter: int) -> Dict[str, Any]:
        """
        Расчет точечных светильников
        
        Args:
            count: Количество светильников
            diameter: Диаметр в мм
            
        Returns:
            Dict с данными о светильниках
        """
        # Подвесы для светильников (по 2 на каждый)
        hangers_count = count * self.coeffs["hangers_per_spotlight"]
        
        return {
            "count": count,
            "diameter": diameter,
            "hangers_count": hangers_count
        }
    
    def calculate_light_lines(self, meters: float, corners: int, crossings: int) -> Dict[str, Any]:
        """
        Расчет световых линий
        
        Args:
            meters: Погонные метры световых линий
            corners: Количество углов 90°
            crossings: Количество перекрестий
            
        Returns:
            Dict с данными о световых линиях
        """
        # Расчет рассеивателя
        corner_margin = corners * self.coeffs["light_line_corner_margin"]
        cross_margin = crossings * self.coeffs["light_line_cross_margin"]
        diffuser_length = meters + corner_margin + cross_margin
        
        return {
            "meters": meters,
            "corners": corners,
            "crossings": crossings,
            "diffuser_length": round(diffuser_length, 2),
            "corner_margin": corner_margin,
            "cross_margin": cross_margin
        }
    
    def calculate_floating_light(self, meters: float) -> Dict[str, Any]:
        """
        Расчет парящей подсветки
        
        Args:
            meters: Погонные метры парящей подсветки
            
        Returns:
            Dict с данными о парящей подсветке
        """
        # Профиль для парящей подсветки = введенным метрам
        profile_meters = meters
        
        # Рассеиватель с запасом 5%
        diffuser_meters = meters * (1 + self.coeffs["floating_diffuser_margin"])
        
        # Дополнительные саморезы (3 на метр)
        additional_screws = math.ceil(meters * self.coeffs["floating_screws_per_meter"])
        
        return {
            "meters": meters,
            "profile_meters": profile_meters,
            "diffuser_meters": round(diffuser_meters, 2),
            "additional_screws": additional_screws,
            "diffuser_margin_percent": self.coeffs["floating_diffuser_margin"] * 100
        }
    
    def calculate_curtain_niche_u_shaped(self, meters: float) -> Dict[str, Any]:
        """
        Расчет П-образной ниши под шторы
        
        Args:
            meters: Погонные метры
            
        Returns:
            Dict с данными о нише
        """
        ends_count = self.coeffs["curtain_ends_count"]  # 2 торца
        tape_meters = meters * self.coeffs["curtain_tape_per_meter"]  # 2м ленты на 1м профиля
        brackets_count = math.ceil(meters * self.coeffs["curtain_brackets_per_meter"])  # 2 на метр
        screws_count = brackets_count * self.coeffs["curtain_screws_per_bracket"]  # 2 на кронштейн
        
        return {
            "meters": meters,
            "ends_count": ends_count,
            "tape_meters": tape_meters,
            "brackets_count": brackets_count,
            "screws_count": screws_count
        }
    
    def calculate_curtain_niche_l_shaped(self, meters: float) -> Dict[str, Any]:
        """
        Расчет Г-образной ниши под шторы
        
        Args:
            meters: Погонные метры
            
        Returns:
            Dict с данными о нише
        """
        ends_count = self.coeffs["curtain_ends_count"]  # 2 торца
        brackets_count = math.ceil(meters * self.coeffs["curtain_brackets_per_meter"])  # 2 на метр
        screws_count = brackets_count * self.coeffs["curtain_screws_per_bracket"]  # 2 на кронштейн
        
        return {
            "meters": meters,
            "ends_count": ends_count,
            "brackets_count": brackets_count,
            "screws_count": screws_count
        }
    
    def calculate_timber(self, meters: float) -> Dict[str, Any]:
        """
        Расчет бруса
        
        Args:
            meters: Погонные метры бруса
            
        Returns:
            Dict с данными о брусе
        """
        brackets_count = math.ceil(meters * self.coeffs["timber_brackets_per_meter"])  # 2 на метр
        
        return {
            "meters": meters,
            "brackets_count": brackets_count
        }
    
    def calculate_totals(self, area: float, perimeter: float, 
                        lighting_data: Dict[str, Any] = None,
                        curtain_data: Dict[str, Any] = None,
                        floating_data: Dict[str, Any] = None,
                        timber_data: Dict[str, Any] = None,
                        profile_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Автоматические расчеты итоговых материалов
        
        Args:
            area: Площадь помещения в м²
            perimeter: Периметр помещения в м
            lighting_data: Данные об освещении
            curtain_data: Данные о нишах под шторы
            floating_data: Данные о парящей подсветке
            timber_data: Данные о брусе
            profile_data: Данные о профиле
            
        Returns:
            Dict с итоговыми расчетами
        """
        # Общее количество подвесов
        base_hangers = math.ceil(area * self.coeffs["hangers_per_sqm"])  # 1 на 2 м²
        lighting_hangers = 0
        
        if lighting_data and lighting_data.get("type") == "spot_lights":
            lighting_hangers = lighting_data.get("hangers_count", 0)
        
        total_hangers = base_hangers + lighting_hangers
        
        # Общее количество дюбелей
        profile_dowels = profile_data.get("dowel_nails_count", 0) if profile_data else 0
        curtain_screws = curtain_data.get("screws_count", 0) if curtain_data else 0
        timber_brackets = timber_data.get("brackets_count", 0) if timber_data else 0
        
        total_dowels = profile_dowels + total_hangers + curtain_screws + timber_brackets
        
        # Общее количество саморезов (клоп-саморезы)
        base_screws = math.ceil(perimeter * self.coeffs["screws_per_perimeter_meter"])  # 4 на метр
        floating_screws = floating_data.get("additional_screws", 0) if floating_data else 0
        curtain_screws_additional = curtain_data.get("screws_count", 0) if curtain_data else 0
        
        total_screws = base_screws + floating_screws + curtain_screws_additional
        
        # Объем клея
        glue_volume = total_hangers * (self.coeffs["glue_ml_per_hanger"] / 1000)  # в литрах
        
        return {
            "total_hangers": total_hangers,
            "base_hangers": base_hangers,
            "lighting_hangers": lighting_hangers,
            "total_dowels": total_dowels,
            "total_screws": total_screws,
            "base_screws": base_screws,
            "floating_screws": floating_screws,
            "curtain_screws": curtain_screws_additional,
            "glue_volume": round(glue_volume, 3)
        }
    
    def format_estimate(self, perimeter: float, area: float, corners_count: int,
                       profile_type: str, profile_data: Dict[str, Any],
                       lighting_type: str, lighting_data: Dict[str, Any],
                       curtain_data: Optional[Dict[str, Any]] = None,
                       timber_data: Optional[Dict[str, Any]] = None,
                       fastener_type: str = None,
                       totals: Dict[str, Any] = None) -> str:
        """
        Формирует итоговую смету
        
        Returns:
            Текст сметы
        """
        estimate = "📋 **СМЕТА НАТЯЖНОГО ПОТОЛКА**\n\n"
        
        # Параметры помещения
        estimate += "🏠 **ПАРАМЕТРЫ ПОМЕЩЕНИЯ:**\n"
        estimate += f"• Периметр: {perimeter:.2f} м\n"
        estimate += f"• Площадь: {area:.2f} м²\n"
        estimate += f"• Количество углов: {corners_count}\n\n"
        
        # Основные материалы
        estimate += "🔨 **ОСНОВНЫЕ МАТЕРИАЛЫ:**\n"
        profile_name = settings.PROFILE_TYPES.get(profile_type, profile_type)
        estimate += f"• Тип профиля: {profile_name}\n"
        estimate += f"• Количество профиля: {profile_data.get('profile_quantity', 0):.2f} м\n"
        estimate += f"• Полотно натяжного потолка: {area:.2f} м²\n\n"
        
        # Освещение
        estimate += "💡 **ОСВЕЩЕНИЕ:**\n"
        lighting_name = settings.LIGHTING_TYPES.get(lighting_type, lighting_type)
        estimate += f"• Тип: {lighting_name}\n"
        
        if lighting_type == "spot_lights":
            estimate += f"• Количество светильников: {lighting_data.get('count', 0)} шт\n"
            estimate += f"• Диаметр: {lighting_data.get('diameter', 0)} мм\n"
            estimate += f"• Дополнительные подвесы: {lighting_data.get('hangers_count', 0)} шт\n"
        elif lighting_type == "light_lines":
            estimate += f"• Длина световых линий: {lighting_data.get('meters', 0)} м\n"
            estimate += f"• Углы 90°: {lighting_data.get('corners', 0)} шт\n"
            estimate += f"• Перекрестья: {lighting_data.get('crossings', 0)} шт\n"
            estimate += f"• Рассеиватель: {lighting_data.get('diffuser_length', 0):.2f} м\n"
        elif lighting_type == "floating_light":
            estimate += f"• Длина парящей подсветки: {lighting_data.get('meters', 0)} м\n"
            estimate += f"• Профиль для подсветки: {lighting_data.get('profile_meters', 0)} м\n"
            estimate += f"• Рассеиватель: {lighting_data.get('diffuser_meters', 0):.2f} м\n"
            estimate += f"• Дополнительные саморезы: {lighting_data.get('additional_screws', 0)} шт\n"
        
        estimate += "\n"
        
        # Дополнительные элементы
        estimate += "➕ **ДОПОЛНИТЕЛЬНЫЕ ЭЛЕМЕНТЫ:**\n"
        
        if curtain_data:
            curtain_type_name = settings.CURTAIN_NICHE_TYPES.get(curtain_data.get('type'), 'Ниша под шторы')
            estimate += f"• {curtain_type_name}: {curtain_data.get('meters', 0)} м\n"
            
            if curtain_data.get('type') == 'u_shaped':
                estimate += f"  - Торцы: {curtain_data.get('ends_count', 0)} шт\n"
                estimate += f"  - Бандажная лента: {curtain_data.get('tape_meters', 0)} м\n"
            
            estimate += f"  - Кронштейны: {curtain_data.get('brackets_count', 0)} шт\n"
            estimate += f"  - Саморезы со сверлом: {curtain_data.get('screws_count', 0)} шт\n"
        else:
            estimate += "• Ниши под шторы: не требуются\n"
        
        if timber_data:
            estimate += f"• Брус: {timber_data.get('meters', 0)} м\n"
            estimate += f"  - Кронштейны: {timber_data.get('brackets_count', 0)} шт\n"
        else:
            estimate += "• Брус: не требуется\n"
        
        estimate += "\n"
        
        # Крепеж и расходники
        estimate += "🔩 **КРЕПЕЖ И РАСХОДНИКИ:**\n"
        
        if fastener_type:
            fastener_name = settings.FASTENER_TYPES.get(fastener_type, fastener_type)
            estimate += f"• Основной крепеж: {fastener_name}\n"
        
        if totals:
            estimate += f"• Дюбели/дюбель-гвозди: {totals.get('total_dowels', 0)} шт\n"
            estimate += f"• Саморезы (клоп): {totals.get('total_screws', 0)} шт\n"
            estimate += f"• Подвесы: {totals.get('total_hangers', 0)} шт\n"
            estimate += f"• Клей: {totals.get('glue_volume', 0):.2f} л\n"
        
        estimate += "\n"
        estimate += "✅ **Смета готова!**"
        
        return estimate


# Создаем экземпляр калькулятора
ceiling_calc = CeilingMaterialsCalculator() 