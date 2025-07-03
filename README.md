# Telegram бот для расчета натяжных потолков

Бот для автоматического распознавания размеров помещений с фотографий и расчета периметра/площади для натяжных потолков с использованием Google Gemini AI.

## Возможности

- 📸 Распознавание рукописных размеров с фотографий
- 📐 Расчет периметра для плинтуса/багета
- 📏 Расчет площади для полотна потолка
- 💳 Система подписок с разными тарифными планами
- 📊 История расчетов для подписчиков
- 🤖 Использование Google Gemini для распознавания

## Технологии

- Python 3.11+
- aiogram 3.x (асинхронный Telegram Bot API)
- Google Gemini AI для распознавания изображений
- SQLite для хранения данных
- YooKassa для приема платежей (опционально)

## Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/yourusername/ceiling-bot.git
cd ceiling-bot
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# Токен бота от @BotFather
BOT_TOKEN=your_bot_token_here

# Имя бота (без @)
BOT_USERNAME=ceiling_calc_bot

# API ключ от Google AI Studio
GEMINI_API_KEY=your_gemini_api_key_here

# YooKassa настройки (опционально)
YOOKASSA_SHOP_ID=
YOOKASSA_SECRET_KEY=

# База данных
DATABASE_URL=sqlite:///bot.db
```

### 5. Получение API ключей

#### Telegram Bot Token:
1. Найдите @BotFather в Telegram
2. Отправьте `/newbot` и следуйте инструкциям
3. Скопируйте полученный токен

#### Google Gemini API Key:
1. Перейдите на [Google AI Studio](https://aistudio.google.com/)
2. Нажмите "Get API key"
3. Создайте новый ключ и скопируйте его

#### YooKassa (опционально):
1. Зарегистрируйтесь на [YooKassa](https://yookassa.ru/)
2. Получите Shop ID и Secret Key в личном кабинете

## Запуск

### Локальный запуск

```bash
python main.py
```

### Docker

```bash
# Сборка образа
docker build -t ceiling-bot .

# Запуск контейнера
docker run -d --name ceiling-bot \
  -e BOT_TOKEN=your_token \
  -e GEMINI_API_KEY=your_key \
  -v $(pwd)/bot.db:/app/bot.db \
  ceiling-bot
```

### Docker Compose

Создайте `docker-compose.yml`:

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: ceiling-bot
    env_file: .env
    volumes:
      - ./bot.db:/app/bot.db
      - ./logs:/app/logs
    restart: unless-stopped
```

Запуск:

```bash
docker-compose up -d
```

## Использование

1. Найдите вашего бота в Telegram по имени пользователя
2. Отправьте `/start` для начала работы
3. Выберите "📐 Рассчитать размеры" в меню
4. Выберите тип расчета (периметр, площадь или оба)
5. Отправьте фото с размерами или введите их вручную
6. Получите результат расчета с учетом припусков

## Тарифные планы

- **Бесплатный**: 2 расчета в день
- **Базовый** (199₽/мес): 50 расчетов в месяц
- **Профи** (399₽/мес): 200 расчетов в месяц  
- **Безлимит** (799₽/мес): Неограниченное количество расчетов

## Структура проекта

```
ceiling_bot/
├── bot/
│   ├── handlers/        # Обработчики команд
│   ├── keyboards/       # Клавиатуры
│   ├── utils/          # Утилиты (Gemini, калькулятор)
│   └── database/       # Модели БД
├── config/             # Настройки
├── main.py            # Точка входа
├── requirements.txt   # Зависимости
└── Dockerfile        # Docker образ
```

## Разработка

### Добавление новых функций

1. Создайте новый handler в `bot/handlers/`
2. Зарегистрируйте router в `main.py`
3. Добавьте необходимые клавиатуры в `bot/keyboards/`

### Логирование

Логи сохраняются в файл `bot.log` и выводятся в консоль.

## Поддержка

При возникновении проблем:
1. Проверьте логи: `tail -f bot.log`
2. Убедитесь, что все API ключи корректны
3. Проверьте доступность API Google Gemini

## Лицензия

MIT License 