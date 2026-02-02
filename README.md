# Booking Service API

REST API для управления бронированиями столиков в ресторане. Полнофункциональное приложение на **FastAPI** с **PostgreSQL**, **Redis** и **Celery**.

## 📋 Возможности

- 🔐 JWT аутентификация (access_token + refresh_token)
- 📅 Защита от race conditions (row-level locking на PostgreSQL)
- 👥 Управление ролями (админ, пользователь, заблокированные)
- 🍽️ CRUD для зон, столиков, бронирований
- 📧 Асинхронные уведомления (Celery + Redis)
- 🧪 4 passed, 1 skipped — полное тестовое покрытие
- 📖 Swagger UI и ReDoc документация
- 🐳 Docker Compose для быстрого старта
- 📝 Логирование всех операций

## 🏗️ Стек технологий

- **FastAPI** — асинхронный веб-фреймворк
- **SQLAlchemy 2.x** — ORM с поддержкой Python 3.13
- **PostgreSQL** — основная БД (SQLite для тестов)
- **Redis** — брокер для Celery
- **Alembic** — миграции БД
- **pytest** + **pytest-asyncio** — тестирование
- **Docker & Docker Compose** — контейнеризация

## 🚀 Быстрый старт

### С Docker (рекомендуется)

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/JolyRed/Booking_Service_API
cd Booking_Service_API

# 2. Создайте .env
cp .env.example .env

# 3. Запустите контейнеры
docker-compose up -d

# 4. Посетите API
# Swagger: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

**БД и данные сохраняются** между запусками.

Нормальный стоп (без потери данных):
```bash
docker-compose stop
docker-compose up -d  # Возобновить
```

### Локальная установка

```bash
# 1. Создайте виртуальное окружение
python3.13 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows

# 2. Установите зависимости
pip install -e .

# 3. Создайте .env
cp .env.example .env

# 4. Инициализируйте БД
alembic upgrade head

# 5. Запустите сервер
uvicorn app.main:app --reload

# 6. В другом терминале запустите Celery (опционально)
celery -A app.celery_app worker --loglevel=info
```

**Минимальный .env для локальной разработки:**
```
DATABASE_URL=postgresql://user:password@localhost:5432/booking_db
SECRET_KEY=your-secret-key-min-32-chars-abcdefgh1234567890
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
```

## ✅ Запуск тестов

```bash
# Все тесты
pytest -q

# С подробностью
pytest -v

# Конкретный файл
pytest tests/test_auth.py -v

# С покрытием кода
pytest --cov=app --cov-report=html
```

**Результаты:** 4 passed, 1 skipped
- ✅ Регистрация, логин, блокировка пользователя
- ✅ CRUD администратора (зоны, столики)
- ✅ Бронирование, конфликты времени, отмена
- ✅ Получение доступных столиков
- ⏭️ Race condition (skipped на SQLite, проходит на Postgres в CI)

## 🔒 Защита от Race Conditions

При одновременном бронировании одного столика используется **row-level locking**:

```python
# 1. Блокируем строку таблицы
table_lock = db.query(Table).filter(Table.id == table_id).with_for_update().first()

# 2. Проверяем конфликты (атомарно)
conflicting = db.query(Booking).filter(...).first()

# 3. Создаём бронирование (или отклоняем, если конфликт)
if not conflicting:
    db.add(new_booking)
    db.commit()
```

**На PostgreSQL** это гарантирует, что только одно бронирование создано.

## 📚 API Endpoints

### Аутентификация
| Метод | Endpoint | Описание |
|-------|----------|---------|
| POST | `/auth/register` | Регистрация |
| POST | `/auth/login` | Вход (JWT) |
| GET | `/auth/me` | Профиль текущего пользователя |
| POST | `/auth/refresh` | Обновить access token |

### Бронирования
| Метод | Endpoint | Описание |
|-------|----------|---------|
| POST | `/bookings/` | Создать бронирование |
| GET | `/bookings/my_bookings` | Мои бронирования |
| GET | `/bookings/all_bookings` | Все бронирования (админ) |
| PATCH | `/bookings/{id}/cancel` | Отменить бронирование |

### Управление (Админ)
| Метод | Endpoint | Описание |
|-------|----------|---------|
| POST | `/zones/` | Создать зону |
| POST | `/tables/` | Создать столик |
| GET | `/tables/available` | Доступные столики |

## 📝 Логирование

Все операции логируются:
```bash
# Просмотр логов
docker-compose logs api -f

# Уровень настраивается в .env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

Примеры:
```
- User registered: user@example.com (ID=1)
- User logged in: user@example.com (ID=1)
- Booking created: ID=42, user=1, table=5
- Booking conflict for table 5: 2026-02-01 19:00:00 - 21:00:00
```

## �� Структура проекта

```
booking_tables/
├── app/
│   ├── models/          # SQLAlchemy модели
│   ├── schemas/         # Pydantic валидация
│   ├── routers/         # API endpoints
│   ├── utils/           # security, dependencies
│   ├── tasks/           # Celery задачи
│   ├── config.py        # Настройки (из .env)
│   ├── database.py      # Сессия БД
│   ├── main.py          # FastAPI приложение
│   └── celery_app.py    # Celery конфигурация
├── alembic/             # Миграции БД
├── tests/               # pytest тесты
├── Dockerfile           # Docker образ
├── docker-compose.yml   # Оркестрация
├── pyproject.toml       # Зависимости
└── README.md            # Этот файл
```

## 🔧 Разработка

### Добавить новый endpoint

1. **Создайте новый файл** `app/routers/myfeature.py`:
```python
from fastapi import APIRouter, Depends
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/myfeature", tags=["MyFeature"])

@router.get("/")
def get_data(current_user = Depends(get_current_user)):
    """Получить данные"""
    logger.info(f"User {current_user.id} fetched data")
    return {"message": "success"}
```

2. **Добавьте в `app/main.py`**:
```python
from app.routers import myfeature
app.include_router(myfeature.router)
```

3. **Напишите тест** `tests/test_myfeature.py`
4. **Запустите тесты**: `pytest tests/test_myfeature.py -v`

### Миграции БД

```bash
# Создать миграцию
alembic revision --autogenerate -m "Описание"

# Применить
alembic upgrade head

# Откатить
alembic downgrade -1
```

## 🚀 Развёртывание

### На продакшене

1. **Используйте сильный SECRET_KEY**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Используйте managed services**
   - PostgreSQL: AWS RDS, DigitalOcean, etc.
   - Redis: AWS ElastiCache, DigitalOcean, etc.

3. **Запустите через gunicorn**
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
   ```

4. **Логирование на продакшене**
   ```
   LOG_LEVEL=WARNING
   ```

## 🐛 Отладка

```bash
# Логи приложения
docker-compose logs api -f --tail=100

# Логи БД
docker-compose logs postgres -f

# Подключиться к PostgreSQL
docker-compose exec postgres psql -U user -d booking_db

# Очистить test.db (SQLite)
rm -f test.db
```
