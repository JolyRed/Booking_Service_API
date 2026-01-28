from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from starlette.status import HTTP_201_CREATED, HTTP_200_OK

from app.database import get_db
from app.schemas.table import TableCreate, TableResponse
from app.models import Table, User
from app.utils.dependencies import get_current_admin

from typing import List

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

@router.put("/{table_id}/update", response_model=TableResponse, status_code=HTTP_201_CREATED)
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

@router.delete("/{table_id}/delete", status_code=HTTP_200_OK)
def delete_table(table_id: int, current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    """ удаление столика """
    table = db.query(Table).filter(table_id == Table.id).first()

    if not table:
        raise HTTPException(status_code=404, detail="Такого столика нет")

    db.delete(table)
    db.commit()

    return {"ok": True, "message": "Столик удалён"}
