# Docker инструкция

## Быстрый старт

### 1. Установите Docker и Docker Compose
```bash
# Linux/Mac
curl -fsSL https://get.docker.com -o get-docker.sh | sh

# Windows
# Скачайте Docker Desktop с https://www.docker.com/products/docker-desktop
```

### 2. Запустите контейнеры
```bash
docker-compose up -d
```

Это запустит:
- **PostgreSQL** на порту 5432
- **Redis** на порту 6379
- **FastAPI** на порту 8000
- **Celery Worker** для асинхронных задач
- **Celery Beat** для планировщика задач

### 3. Проверьте статус
```bash
docker-compose ps
```

### 4. Посетите API
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Полезные команды

### Логи
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f api
docker-compose logs -f celery_worker
```

### Остановка
```bash
docker-compose down
```

### Очистка (удалить том с данными)
```bash
docker-compose down -v
```

### Запуск команд в контейнере
```bash
# Интерактивный shell в контейнере API
docker-compose exec api bash

# Запуск команд
docker-compose exec api alembic current
docker-compose exec api python -c "from app.config import settings; print(settings)"
```

### Пересборка образа
```bash
docker-compose build --no-cache
```

### Просмотр БД в контейнере
```bash
docker-compose exec postgres psql -U postgres -d booking_db
```

## Структура

```
docker-compose.yml    # Конфигурация сервисов
Dockerfile           # Образ для FastAPI/Celery
.dockerignore        # Исключаемые файлы при сборке
```

## Переменные окружения

Используются из `.env` или задаются в `docker-compose.yml`:
- `DATABASE_URL`: адрес PostgreSQL
- `SECRET_KEY`: ключ для JWT
- `REDIS_URL`: адрес Redis

## Миграции БД

При запуске контейнера `api` автоматически:
1. Запускает миграции (`alembic upgrade head`)
2. Стартует FastAPI приложение

## Production

Для production используйте:
```bash
# Отключите --reload в uvicorn
command: uvicorn app.main:app --host 0.0.0.0 --port 8000

# Используйте gunicorn
# pip install gunicorn
# command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

## Troubleshooting

### Ошибка подключения к БД
```
Попробуйте перезапустить контейнер:
docker-compose restart api
```

### Миграции не применяются
```bash
docker-compose exec api alembic upgrade head
```

### Очистить кэш Redis
```bash
docker-compose exec redis redis-cli FLUSHALL
```

### Посмотреть переменные в контейнере
```bash
docker-compose exec api env | grep DATABASE_URL
```
