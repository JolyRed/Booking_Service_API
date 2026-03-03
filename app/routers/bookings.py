import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Booking, Table, User
from app.schemas.booking import BookingCreate, BookingResponse
from app.utils.dependencies import get_current_admin, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создание бронирования

    - Блокирует строку таблицы для атомарности проверки конфликтов
    - Проверяет пересечение времени с существующими бронированиями
    - Отправляет асинхронное уведомление при успехе
    """
    logger.info(
        f"User {current_user.id} attempting to book table {booking_data.table_id}"
    )

    # Проверить, что time_start < time_stop
    if booking_data.time_start >= booking_data.time_stop:
        logger.warning(
            f"Invalid time range: {booking_data.time_start} >= {booking_data.time_stop}"
        )
        raise HTTPException(
            status_code=400,
            detail="Время начала бронирования должно быть меньше, чем время окончания",
        )

    # Проверить, что столик свободен
    # Критический момент: блокируем строку таблицы для атомарности проверки + вставки
    # Это гарантирует, что два одновременных запроса не пройдут одновременно
    table_lock = (
        db.query(Table)
        .filter(Table.id == booking_data.table_id)
        .with_for_update()
        .first()
    )
    if not table_lock:
        logger.warning(f"Table {booking_data.table_id} not found")
        raise HTTPException(status_code=404, detail="Столик не найден")

    # Теперь проверяем конфликты (под защитой блокировки таблицы)
    conflicting_booking = (
        db.query(Booking)
        .filter(
            Booking.table_id == booking_data.table_id,
            Booking.status != "cancelled",
            Booking.time_start < booking_data.time_stop,
            Booking.time_stop > booking_data.time_start,
        )
        .first()
    )

    if conflicting_booking:
        logger.warning(
            f"Booking conflict for table {booking_data.table_id}: {conflicting_booking.time_start} - {conflicting_booking.time_stop}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Столик занят с {conflicting_booking.time_start} до {conflicting_booking.time_stop}",
        )

    # Создание бронирования
    new_booking = Booking(
        table_id=booking_data.table_id,
        user_id=current_user.id,
        count_people=booking_data.count_people,
        time_start=booking_data.time_start,
        time_stop=booking_data.time_stop,
        status="pending",
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    logger.info(
        f"Booking created: ID={new_booking.id}, user={current_user.id}, table={booking_data.table_id}"
    )

    from app.tasks import send_booking_confirmation

    send_booking_confirmation.delay(new_booking.id)

    return new_booking


# бронирования одного пользователя
@router.get("/my_bookings", response_model=List[BookingResponse])
def get_my_bookings(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Получить все бронирования текущего пользователя"""
    bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    logger.debug(f"Retrieved {len(bookings)} bookings for user {current_user.id}")
    return bookings


# бронирования для админа
@router.get("/all_bookings", response_model=List[BookingResponse])
def get_all_bookings(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)
):
    """Получить все бронирования (только для админов)"""
    bookings = db.query(Booking).all()
    logger.debug(f"Admin {current_user.id} retrieved all {len(bookings)} bookings")
    return bookings


# отмена бронирования
@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Отменить своё бронирование"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        logger.warning(f"Booking {booking_id} not found")
        raise HTTPException(status_code=404, detail="Бронирование не найдено")

    # Проверить, что бронирование принадлежит текущему пользователю
    if booking.user_id != current_user.id:
        logger.warning(
            f"User {current_user.id} attempted to cancel booking {booking_id} of user {booking.user_id}"
        )
        raise HTTPException(status_code=403, detail="Это не ваше бронирование")

    # Проверить, что статус не cancelled
    if booking.status == "cancelled":
        logger.warning(f"Booking {booking_id} is already cancelled")
        raise HTTPException(status_code=400, detail="Это бронирование уже отменено")

    # Изменить статус на cancelled
    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)

    logger.info(f"Booking {booking_id} cancelled by user {current_user.id}")
    from app.tasks import send_booking_cancellation

    send_booking_cancellation.delay(booking.id)
    return booking
