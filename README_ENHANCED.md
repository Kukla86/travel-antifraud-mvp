# 🚀 Enhanced Travel Antifraud MVP

Полнофункциональная система antifraud для тревел-агентств с ML, real-time мониторингом и enterprise-функциями.

## 🎯 Что добавлено в Enhanced версии

### 🔥 Критичные улучшения
- **Redis** для кэширования и rate limiting
- **WebSocket** для real-time уведомлений
- **JWT аутентификация** с ролями пользователей
- **Индексы БД** для производительности
- **Connection pooling** для SQLite

### 🔐 Безопасность
- **JWT токены** вместо простого API-ключа
- **Audit logging** всех действий
- **Роли пользователей** (admin, analyst)
- **IP whitelist** для дашборда
- **Rate limiting** по device fingerprint

### 📊 Мониторинг и аналитика
- **Real-time метрики** с WebSocket
- **Графики risk distribution** по времени
- **Топ подозрительных IP/email**
- **Статистика по правилам** antifraud
- **Hourly metrics** и тренды
- **Push уведомления** для high-risk транзакций

### 🤖 ML и продвинутая аналитика
- **Anomaly detection** для поведенческих метрик
- **Feature engineering** (typing speed, session patterns)
- **Historical baseline** для сравнения
- **Auto-tuning** порогов на основе данных
- **Clustering** подозрительных паттернов

### 🐳 DevOps и масштабирование
- **Docker контейнеризация** с docker-compose
- **CI/CD pipeline** с GitHub Actions
- **Security scanning** с Trivy
- **Health checks** и мониторинг
- **Production-ready** конфигурация

### 🎨 UX улучшения
- **Real-time обновления** дашборда
- **Push уведомления** в браузере
- **Advanced search** с фильтрами
- **Responsive design** с Tailwind
- **Dark/light theme** поддержка

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Redis         │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Cache)       │
│   - Dashboard   │    │   - API         │    │   - Rate Limit  │
│   - WebSocket   │    │   - WebSocket   │    │   - Sessions    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │                       ▼
         │              ┌─────────────────┐
         │              │   SQLite        │
         │              │   - Fraud Logs  │
         │              │   - ML Models   │
         │              │   - Audit Logs  │
         │              └─────────────────┘
         │
         ▼
┌─────────────────┐
│   External      │
│   - ipapi.co    │
│   - Notifications│
└─────────────────┘
```

## 🚀 Быстрый старт

### 1. Локальная разработка
```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Redis (отдельный терминал)
docker run -d -p 6379:6379 redis:7-alpine

# Dashboard
cd dashboard
npm install
npm run dev
```

### 2. Docker (рекомендуется)
```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Логи
docker-compose logs -f
```

### 3. Production деплой
```bash
# Сборка образов
docker-compose -f docker-compose.prod.yml build

# Запуск в production
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 API Endpoints

### Аутентификация
- `POST /api/auth/login` - Вход в систему
- `GET /api/auth/me` - Информация о пользователе

### Antifraud
- `POST /api/check` - Проверка транзакции
- `GET /api/checks` - Список проверок
- `GET /api/checks/{id}` - Детали проверки

### Blacklist
- `POST /api/blacklist` - Добавить IP
- `GET /api/blacklist` - Список IP
- `DELETE /api/blacklist/{id}` - Удалить IP

### Аналитика
- `GET /api/analytics/risk-distribution` - Распределение рисков
- `GET /api/analytics/top-fraud-flags` - Топ флагов
- `GET /api/analytics/suspicious-ips` - Подозрительные IP
- `GET /api/analytics/hourly-metrics` - Метрики по часам
- `GET /api/analytics/rule-performance` - Эффективность правил

### ML
- `GET /api/ml/anomalies` - Список аномалий
- `POST /api/ml/retrain` - Переобучение модели

### WebSocket
- `WS /ws` - Real-time соединение

## 🎛️ Дашборд функции

### 📊 Real-time метрики
- Общее количество проверок
- High-risk транзакции
- Blacklisted IP адреса
- Размер кэша

### 📈 Аналитика
- **Risk Distribution** - распределение по уровням риска
- **Top Fraud Flags** - самые частые флаги мошенничества
- **Suspicious IPs** - подозрительные IP адреса
- **Hourly Metrics** - метрики по часам
- **Rule Performance** - эффективность правил

### 🔍 Фильтры и поиск
- По email, IP, флагам
- По датам (от/до)
- Advanced search с regex
- Сохранение view preferences

### ⚡ Real-time функции
- **WebSocket** соединение для live обновлений
- **Push уведомления** для high-risk транзакций
- **Auto-refresh** метрик каждые 30 секунд
- **Live fraud alerts** в реальном времени

## 🤖 ML и Anomaly Detection

### Признаки для ML
- **Typing speed** - скорость печати
- **Session duration** - длительность сессии
- **Mouse movements** - движения мыши
- **First click delay** - задержка первого клика
- **Device fingerprint frequency** - частота использования отпечатка

### Алгоритмы
- **Anomaly Detection** - обнаружение аномалий
- **Feature Engineering** - извлечение признаков
- **Historical Baseline** - исторические данные
- **Auto-tuning** - автоматическая настройка порогов

## 🔐 Безопасность

### Аутентификация
- **JWT токены** с истечением
- **Роли пользователей** (admin, analyst)
- **Password hashing** с bcrypt
- **Session management**

### Audit Logging
- Все действия логируются
- IP адрес и User-Agent
- Timestamp и детали
- Поиск по логам

### Rate Limiting
- **Per IP** - 60 запросов/минуту
- **Per Email** - 20 запросов/минуту
- **Per Device** - 30 запросов/минуту
- **Sliding window** алгоритм

## 📊 Мониторинг

### Health Checks
- `GET /health` - Статус системы
- `GET /metrics` - Детальные метрики
- **Redis connectivity** проверка
- **Database** health check

### Логирование
- **JSON structured logs**
- **Correlation IDs** для трейсинга
- **Log levels** (DEBUG, INFO, WARN, ERROR)
- **File rotation** и retention

### Алертинг
- **High-risk transaction** алерты
- **System health** мониторинг
- **Rate limit** превышения
- **ML model** performance

## 🧪 Тестирование

### Backend тесты
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend тесты
```bash
cd dashboard
npm run test:unit
```

### Integration тесты
```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🚀 Production Deployment

### Environment Variables
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/antifraud

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# CORS
CORS_ORIGINS=https://yourdomain.com

# ML
ML_MODEL_PATH=/app/models
ML_RETRAIN_SCHEDULE=0 2 * * *
```

### Docker Production
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    image: antifraud-backend:latest
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

### Kubernetes
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: antifraud-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: antifraud-backend
  template:
    spec:
      containers:
      - name: backend
        image: antifraud-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: antifraud-secrets
              key: database-url
```

## 📈 Масштабирование

### Горизонтальное масштабирование
- **Load balancer** (nginx/HAProxy)
- **Multiple backend** instances
- **Redis Cluster** для кэша
- **Database sharding** по датам

### Вертикальное масштабирование
- **CPU/Memory** оптимизация
- **Connection pooling** для БД
- **Caching strategies** (Redis, CDN)
- **Query optimization** с индексами

## 🔧 Конфигурация

### Backend настройки
```python
# app/config.py
class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///antifraud.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # JWT
    jwt_secret_key: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Rate Limiting
    rate_limit_ip: int = 60
    rate_limit_email: int = 20
    
    # ML
    ml_model_path: str = "/app/models"
    anomaly_threshold: float = 0.7
    
    # Logging
    log_level: str = "INFO"
    log_retention_days: int = 90
```

### Frontend настройки
```javascript
// dashboard/src/config.js
export const config = {
  apiBase: process.env.VITE_API_BASE || 'http://localhost:8000',
  wsUrl: process.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  enableNotifications: true,
  refreshInterval: 30000,
  theme: 'light' // 'light' | 'dark'
}
```

## 🎯 Roadmap

### v2.0 (Q2 2024)
- [ ] **GraphQL API** для гибких запросов
- [ ] **Microservices** архитектура
- [ ] **Event Sourcing** для аудита
- [ ] **CQRS** для чтения/записи

### v2.1 (Q3 2024)
- [ ] **Advanced ML** модели (LSTM, Transformer)
- [ ] **Real-time streaming** (Kafka)
- [ ] **Multi-tenant** поддержка
- [ ] **API versioning** стратегия

### v3.0 (Q4 2024)
- [ ] **Federated learning** для ML
- [ ] **Edge computing** поддержка
- [ ] **Blockchain** интеграция
- [ ] **Quantum-resistant** криптография

## 🤝 Contributing

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл.

## 🆘 Поддержка

- **Documentation**: [docs.antifraud.com](https://docs.antifraud.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/antifraud/issues)
- **Discord**: [Antifraud Community](https://discord.gg/antifraud)
- **Email**: support@antifraud.com

---

**🚀 Enhanced Travel Antifraud MVP** - Enterprise-ready система защиты от мошенничества с ML, real-time мониторингом и современной архитектурой!
