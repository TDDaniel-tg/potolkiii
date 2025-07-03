# 🚀 Деплой бота на Railway через GitHub

## 📋 Подготовка к деплою

### 1. 🔐 Переменные окружения (Environment Variables)

В Railway нужно установить следующие переменные:

```bash
# Обязательные переменные
BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here

# Опциональные переменные (для платежей)
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key

# Настройки базы данных (автоматически)
DATABASE_URL=sqlite:///bot.db
```

### 2. 📁 Файлы конфигурации (уже созданы)

- ✅ `railway.json` - основная конфигурация Railway
- ✅ `nixpacks.toml` - настройки сборки Python
- ✅ `requirements.txt` - зависимости Python
- ✅ `.gitignore` - исключения для Git
- ✅ `main.py` - точка входа приложения

---

## 🛠 Пошаговая инструкция

### Шаг 1: Подготовка GitHub репозитория

1. **Создайте новый репозиторий на GitHub:**
   - Название: `potolki-bot` (или любое другое)
   - Сделайте его приватным для безопасности

2. **Загрузите код в репозиторий:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Potolki ceiling calculator bot"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/potolki-bot.git
   git push -u origin main
   ```

### Шаг 2: Настройка Railway

1. **Зайдите на [railway.app](https://railway.app)**
2. **Войдите через GitHub аккаунт**
3. **Создайте новый проект:**
   - Нажмите "New Project"
   - Выберите "Deploy from GitHub repo"
   - Выберите репозиторий `potolki-bot`

### Шаг 3: Настройка переменных окружения

В Railway в разделе **Variables** добавьте:

```
BOT_TOKEN = 7xxxxxxx:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY = AIxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Где взять токены:**

#### 🤖 BOT_TOKEN:
1. Напишите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен

#### 🧠 GEMINI_API_KEY:
1. Перейдите на [Google AI Studio](https://aistudio.google.com/)
2. Нажмите "Get API key"
3. Создайте новый ключ
4. Скопируйте ключ

### Шаг 4: Деплой

1. **Railway автоматически начнет деплой** после настройки переменных
2. **Дождитесь завершения сборки** (2-5 минут)
3. **Проверьте логи** на наличие ошибок

---

## 🔧 Настройки админов

**Текущие админы (безлимитные подписки):**
- `5123262366` ✅
- `545371253` ✅  
- `6733176057` ✅

**Админские команды:**
- `/admin` - справка
- `/unlimited <user_id>` - безлимитная подписка
- `/set_sub <user_id> <type> [days]` - установка подписки
- `/user_info <user_id>` - информация о пользователе

---

## 📊 Мониторинг

### Логи Railway:
- Перейдите в проект на Railway
- Откройте вкладку "Deployments"
- Нажмите на последний деплой
- Смотрите логи в реальном времени

### Основные метрики:
- **Статус бота:** Должен показывать "Running"
- **Использование памяти:** ~100-200 MB
- **Использование CPU:** ~5-10%

---

## 🔄 Обновление бота

### Для обновления кода:

1. **Внесите изменения в локальный код**
2. **Загрузите в GitHub:**
   ```bash
   git add .
   git commit -m "Update: описание изменений"
   git push
   ```
3. **Railway автоматически перезапустит бот**

---

## 🛡 Безопасность

### ⚠️ ВАЖНО:
- **Никогда не комитьте `.env` файл** в Git
- **Используйте только переменные окружения** Railway
- **Сделайте репозиторий приватным**
- **Регулярно обновляйте токены**

### 🔐 Переменные окружения в Railway:
```
BOT_TOKEN = ваш_токен_бота
GEMINI_API_KEY = ваш_ключ_gemini
YOOKASSA_SHOP_ID = ваш_shop_id (опционально)
YOOKASSA_SECRET_KEY = ваш_secret_key (опционально)
```

---

## 📞 Поддержка

### При проблемах проверьте:

1. **Переменные окружения** правильно установлены
2. **Токен бота** действителен
3. **Gemini API ключ** активен
4. **Логи Railway** на наличие ошибок

### Полезные ссылки:
- [Railway Docs](https://docs.railway.app/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Google AI Studio](https://aistudio.google.com/)

---

## 🎉 Готово!

После успешного деплоя ваш бот будет доступен 24/7 на Railway!

**URL деплоя:** Railway предоставит автоматически  
**Домен:** Можно настроить кастомный домен в настройках проекта

✅ **Бот готов к работе!** 