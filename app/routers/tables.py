from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, not_

from app.database import get_db
from app.schemas.table import TableCreate, TableResponse
from app.models import Table, User, Booking
from app.utils.dependencies import get_current_admin

from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/tables", tags=["Tables"])

@router.post("/", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
def create_table(
        table_data: TableCreate,
        current_user: User = Depends(get_current_admin),
        db: Session = Depends(get_db)
):

    """
    добавление нового столика
    """
    is_table = db.query(Table).filter(Table.number == table_data.number).first() # проверка на наличие столика в базе

    if is_table:
        raise HTTPException(status_code=400, detail="Такой столик уже есть")

    new_table = Table(
        number=table_data.number,
        count_place=table_data.count_place,
        zone_id=table_data.zone_id,
    )

    db.add(new_table)
    db.commit()
    db.refresh(new_table)

    return new_table


@router.get("/", response_model=List[TableResponse])
def get_all_tables(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    all_tables = db.query(Table).all()

    if not all_tables:
        raise HTTPException(status_code=404, detail="Столиков нет")

    return all_tables

@router.put("/{table_id}/update", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
def update_table(table_id: int, table_data: TableCreate, current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    """ обновление столика """
    table = db.query(Table).filter(table_id == Table.id).first()

    if not table:
        raise HTTPException(status_code=404, detail="Такого столика нет")

    table.number = table_data.number
    table.count_place = table_data.count_place
    table.zone_id = table_data.zone_id

    db.commit()
    db.refresh(table)

    return table

@router.delete("/{table_id}/delete", status_code=status.HTTP_200_OK)
def delete_table(table_id: int, current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    """ удаление столика """
    table = db.query(Table).filter(table_id == Table.id).first()

    if not table:
        raise HTTPException(status_code=404, detail="Такого столика нет")

    db.delete(table)
    db.commit()

    return {"ok": True, "message": "Столик удалён"}

@router.get("/available", response_model=List[TableResponse])
# поиск по фильтрам
def get_available_tables(
        date: str,
        time_start: str,
        time_stop: str,
        zone_id: Optional[int] = None,
        min_seats: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
        db: Session = Depends(get_db)
):
    # парсим дату и время
    try:
        booking_date = datetime.strptime(date, "%Y-%m-%d").date()
        time_start = datetime.strptime(time_start, "%H:%M").time()
        time_stop = datetime.strptime(time_stop, "%H:%M").time()

    # создаём полные datetime объекты

        booking_start = datetime.combine(booking_date, time_start)
        booking_stop = datetime.combine(booking_date, time_stop)

    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты/времени. Используйте YYYY-MM-DD и HH:MM")
    # проверка на корректное время
    if booking_start >= booking_stop:
        raise HTTPException(status_code=400, detail="Время начала должно быть раньше, чем время окончания.")
    # базовый запрос
    query = db.query(Table)
    # фильтр по зоне
    if zone_id is not None:
        query = query.filter(Table.zone_id == zone_id)
    # фильтр по местам
    if min_seats is not None:
        query = query.filter(Table.count_place >= min_seats)

    # поиск занятых столиков
    occupied_tables_subquery = (
        db.query(Booking.table_id).filter(
            Booking.status != "cancelled",
            Booking.time_start < booking_stop,
            Booking.time_stop > booking_start
        ).subquery()
    )
    # исключить занятые столики
    query = query.filter(
        not_(Table.id.in_(occupied_tables_subquery))
    )
    # пагинация
    tables = query.limit(limit).offset(offset).all()

    return tables