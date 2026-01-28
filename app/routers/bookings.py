from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.booking import BookingResponse, BookingCreate
from app.models import Booking, User, Table
from app.utils.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
        booking_data: BookingCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Создание бронирования"""

    # Проверить существует ли столик
    is_table = db.query(Table).filter(Table.id == booking_data.table_id).first()
    if not is_table:
        raise HTTPException(status_code=404, detail="Столик не найден")

    # Проверить, что time_start < time_stop
    if booking_data.time_start >= booking_data.time_stop:
        raise HTTPException(
            status_code=400,
            detail="Время начала бронирования должно быть меньше, чем время окончания"
        )

    # Проверить, что столик свободен
    # Критический момент. Тут нужно проверять занятость с блокировкой
    conflicting_booking = db.query(Booking).filter(
        Booking.table_id == booking_data.table_id,
        Booking.status != "cancelled",
        Booking.time_start < booking_data.time_stop,
        Booking.time_stop > booking_data.time_start
    ).with_for_update().first()

    if conflicting_booking:
        raise HTTPException(
            status_code=400,
            detail=f"Столик занят с {conflicting_booking.time_start} до {conflicting_booking.time_stop}"
        )

    # Создание бронирования
    new_booking = Booking(
        table_id=booking_data.table_id,
        user_id=current_user.id,
        count_people=booking_data.count_people,
        time_start=booking_data.time_start,
        time_stop=booking_data.time_stop,
        status="pending"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    from app.tasks import send_booking_notification
    send_booking_notification.delay(new_booking.id)

    return new_booking


# бронирования одного пользователя
@router.get("/my_bookings", response_model=List[BookingResponse])
def get_my_bookings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    booking = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    return booking

# бронирования для админа
@router.get("/all_bookings", response_model=List[BookingResponse])
def get_all_bookings(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    # реализовать проверку на админа
    booking = db.query(Booking).all()
    return booking


# отмена бронирования
@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(booking_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # поиск бронировани по id
    booking = db.query(Booking).filter(booking_id == Booking.id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    # броверить, что бронирование пренодлежит текущему пользователю
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Это не ваше бронирования")
    # проверить, что статус не cancelled
    if booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Это бронирование уже отменено")
    # изменить статус на cancelled
    booking.status = "cancelled"
    # сохранить и вернуть
    db.commit()
    db.refresh(booking)
    return booking

