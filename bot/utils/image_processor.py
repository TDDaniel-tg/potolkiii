from PIL import Image
import io
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Обработчик изображений для подготовки к распознаванию"""
    
    # Максимальные размеры для оптимизации
    MAX_WIDTH = 1920
    MAX_HEIGHT = 1920
    
    # Поддерживаемые форматы
    SUPPORTED_FORMATS = {
        'JPEG', 'JPG', 'PNG', 'WEBP', 'HEIC', 'HEIF', 'BMP', 'GIF'
    }
    
    async def process_image(self, image_data: bytes) -> Optional[bytes]:
        """
        Обрабатывает изображение для оптимальной работы с API
        
        Args:
            image_data: Байты изображения
            
        Returns:
            Обработанные байты изображения или None при ошибке
        """
        try:
            # Открываем изображение
            image = Image.open(io.BytesIO(image_data))
            
            # Конвертируем в RGB если нужно
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # Изменяем размер если слишком большое
            image = self._resize_if_needed(image)
            
            # Сохраняем в буфер
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='JPEG', quality=85, optimize=True)
            output_buffer.seek(0)
            
            return output_buffer.read()
            
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {e}")
            return None
    
    def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        """Изменяет размер изображения если оно слишком большое"""
        width, height = image.size
        
        if width <= self.MAX_WIDTH and height <= self.MAX_HEIGHT:
            return image
        
        # Вычисляем коэффициент масштабирования
        scale = min(self.MAX_WIDTH / width, self.MAX_HEIGHT / height)
        
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    async def validate_image(self, image_data: bytes) -> Tuple[bool, str]:
        """
        Проверяет валидность изображения
        
        Returns:
            (is_valid, error_message)
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Проверяем формат
            if image.format and image.format.upper() not in self.SUPPORTED_FORMATS:
                return False, f"Формат {image.format} не поддерживается. Используйте JPG, PNG или WEBP."
            
            # Проверяем размер файла (10 MB)
            if len(image_data) > 10 * 1024 * 1024:
                return False, "Размер файла превышает 10 МБ. Пожалуйста, уменьшите изображение."
            
            # Проверяем минимальные размеры
            width, height = image.size
            if width < 100 or height < 100:
                return False, "Изображение слишком маленькое. Минимальный размер 100x100 пикселей."
            
            return True, ""
            
        except Exception as e:
            return False, f"Не удалось открыть изображение: {str(e)}"
    
    def get_image_info(self, image_data: bytes) -> dict:
        """Получает информацию об изображении"""
        try:
            image = Image.open(io.BytesIO(image_data))
            return {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'file_size': len(image_data)
            }
        except:
            return {}


# Создаем экземпляр обработчика
image_processor = ImageProcessor() 