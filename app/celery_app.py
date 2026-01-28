from celery import Celery
from app.config import settings

# Получаем Redis URL из конфига или используем дефолт
redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')

celery_app = Celery(
    "booking_service",
    broker=redis_url,  # Redis как брокер
    backend=redis_url  # Redis для хранения результатов
)

# настройки celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# автоматический поиск задач в модуле tasks
celery_app.autodiscover_tasks(["app.tasks"])
