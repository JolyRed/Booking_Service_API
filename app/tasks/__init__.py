from pathlib import Path

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Booking, Table, User, Zone
from app.utils.email import send_email


def render_template(template_name: str, **context) -> str:
    """Простой рендеринг HTML шаблона"""
    template_path = Path(__file__).parent.parent / "templates" / template_name

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Простая замена переменных {{variable}}
    for key, value in context.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))

    return template


@celery_app.task
def send_booking_confirmation(booking_id: int):
    """Отправка подтверждения бронирования"""
    db = SessionLocal()

    try:
        # Получаем данные бронирования с JOIN'ами
        booking = db.query(Booking).filter(Booking.id == booking_id).first()

        if not booking:
            print(f"❌ Бронирование #{booking_id} не найдено")
            return

        user = db.query(User).filter(User.id == booking.user_id).first()
        table = db.query(Table).filter(Table.id == booking.table_id).first()
        zone = db.query(Zone).filter(Zone.id == table.zone_id).first()

        # Форматируем время
        time_start = booking.time_start.strftime("%d.%m.%Y %H:%M")
        time_stop = booking.time_stop.strftime("%H:%M")
        booking_time = f"{time_start} - {time_stop}"

        # Рендерим HTML шаблон
        html_body = render_template(
            "booking_confirmation.html",
            fullname=user.fullname,
            table_number=table.number,
            zone_name=zone.title,
            count_people=booking.count_people,
            booking_time=booking_time,
            status="Подтверждено" if booking.status == "confirmed" else "В ожидании",
        )

        # Отправляем email
        subject = f"Бронирование столика №{table.number} подтверждено"
        success = send_email(user.email, subject, html_body)

        if success:
            print(f"✅ Email отправлен для бронирования #{booking_id}")
        else:
            print(f"❌ Не удалось отправить email для бронирования #{booking_id}")

        return success

    finally:
        db.close()


@celery_app.task
def send_booking_cancellation(booking_id: int):
    """Отправка уведомления об отмене"""
    db = SessionLocal()

    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return

        user = db.query(User).filter(User.id == booking.user_id).first()
        table = db.query(Table).filter(Table.id == booking.table_id).first()

        time_start = booking.time_start.strftime("%d.%m.%Y %H:%M")
        time_stop = booking.time_stop.strftime("%H:%M")
        booking_time = f"{time_start} - {time_stop}"

        html_body = render_template(
            "booking_cancelled.html",
            fullname=user.fullname,
            table_number=table.number,
            booking_time=booking_time,
        )

        subject = "Бронирование отменено"
        success = send_email(user.email, subject, html_body)

        return success

    finally:
        db.close()
