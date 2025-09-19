# Travel Antifraud MVP

## Описание
MVP антифрод инструмента для тревел агентств с интеграцией в checkout страницы для детекции мошеннических бронирований.

## Архитектура
- **Backend**: FastAPI + SQLite
- **Frontend**: React + TailwindCSS
- **Script**: Vanilla JavaScript для сбора данных
- **Dashboard**: React + TailwindCSS

## Функциональность

### Backend API
- `/api/check` - проверка на мошенничество
- `/api/checks` - получение логов проверок
- `/api/metrics` - метрики системы
- `/api/analytics/*` - аналитика и отчеты

### Антифрод правила
- **Geo**: проверка IP vs BIN страны
- **Email**: детекция временных email
- **Velocity**: проверка частоты запросов
- **Bot**: анализ поведения пользователя
- **Device**: фингерпринтинг устройства
- **Blacklist**: проверка заблокированных IP
- **Timezone**: проверка несоответствия часового пояса

### Dashboard
- **Overview**: обзор метрик и трендов
- **Fraud Logs**: таблица с фильтрами
- **Analytics**: детальная аналитика
- **Check Details**: модальное окно с деталями

## Дизайн

**Design based on Tokyo Dark Admin Dashboard template** – адаптировано цветами и компонентами под антифрод систему.

### Цветовая палитра
- **Основной фон**: #0f172a (темно-графитовый)
- **Акценты**: #3b82f6 (синий), #06b6d4 (бирюзовый)
- **Текст**: #e2e8f0 (мягкий белый)
- **Вторичный текст**: #94a3b8 (серый)

### Компоненты
- **Glassmorphism**: полупрозрачные карточки с blur эффектом
- **Градиенты**: акцентные элементы с градиентными заливками
- **Анимации**: плавные переходы и hover эффекты
- **Адаптивность**: мобильная версия с упрощенным интерфейсом

## Установка и запуск

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main_working:app --reload --host 0.0.0.0 --port 8000
```

### Dashboard
```bash
cd dashboard
npm install
npm run dev
```

### Frontend Script
Откройте `frontend/checkout_demo_working.html` в браузере для тестирования.

## API Endpoints

### Проверка на мошенничество
```javascript
POST /api/check
{
  "email": "user@example.com",
  "ip": "192.168.1.1",
  "bin": "4111111111111111",
  "user_agent": "Mozilla/5.0...",
  "timezone": "Europe/Moscow",
  "browser_language": "ru-RU",
  "session_duration": 120,
  "typing_speed": 45,
  "first_click_time": 500,
  "mouse_movements": 25
}
```

### Ответ
```javascript
{
  "check_id": 123,
  "risk_score": 65,
  "fraud_flags": ["temporary_email", "geo_mismatch"],
  "recommendation": "review",
  "created_at": "2024-01-01T12:00:00Z"
}
```

## Конфигурация

Создайте файл `.env` в корне проекта:
```env
DATABASE_URL=sqlite:///./antifraud.db
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
API_KEY=antifraud_dev_key_2024
SEED_BLACKLIST_IPS=192.168.1.100,10.0.0.1
```

## Лицензия
MIT License