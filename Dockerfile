# Build stage
FROM python:3.13-slim as builder

WORKDIR /app

# Устанавливаем зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем pyproject.toml и устанавливаем зависимости
COPY pyproject.toml .
RUN pip install --no-cache-dir --user -e .

# Runtime stage
FROM python:3.13-slim

WORKDIR /app

# Устанавливаем только необходимые рантайм зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные пакеты из builder
COPY --from=builder /root/.local /root/.local

# Добавляем local bin в PATH
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Копируем исходный код
COPY . .

# Создаём скрипт инициализации с retry логикой
RUN cat > /app/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Функция для проверки подключения к БД
wait_for_db() {
    echo "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if pg_isready -h postgres -U postgres -d booking_db 2>/dev/null; then
            echo "PostgreSQL is ready!"
            return 0
        fi
        echo "Attempt $i: PostgreSQL not ready, waiting..."
        sleep 2
    done
    echo "PostgreSQL failed to respond in time"
    exit 1
}

# Ждём БД
wait_for_db

# Применяем миграции
echo "Running migrations..."
alembic upgrade head

# Запускаем приложение
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF

RUN chmod +x /app/entrypoint.sh

# Запускаем скрипт инициализации
CMD ["/app/entrypoint.sh"]
