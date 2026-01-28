from app.celery_app import celery_app
import time

@celery_app.task
def test_task(name: str):
    """ тестовая задача """
    print(f"Задача началась для {name}")
    time.sleep(5)
    print(f"Задача завершена для {name}")
    return f"Привет, {name}! Задача обновлена!"

@celery_app.task
def send_booking_notification(booking_id: int):
    """ отправка уведомлений о бронировании """
    print(f"Отправка уведомения о бронировании {booking_id}")
    time.sleep(3)
    print(f"Уведомление отправлено для бронирования {booking_id}")
    return f"Email send for booking {booking_id}"

