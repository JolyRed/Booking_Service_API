from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Zone
from app.schemas.zones import ZoneCreate, ZoneResponse
from app.utils.dependencies import get_current_admin

router = APIRouter(prefix="/zones", tags=["Zones"])


@router.get("/{zone_id}", response_model=ZoneResponse, status_code=status.HTTP_200_OK)
def get_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    zone = db.query(Zone).filter(zone_id == Zone.id).first()

    if not zone:
        raise HTTPException(status_code=404, detail="Зона не найдена")

    return zone


@router.get("/", response_model=List[ZoneResponse], status_code=status.HTTP_200_OK)
def get_all_zones(
    db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)
):
    """получение всех зон для админа"""
    zones = db.query(Zone).all()

    if not zones:
        return []

    return zones


@router.post("/", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(
    zone_data: ZoneCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """добавление новой зоны"""
    existing_zone = db.query(Zone).filter(zone_data.title == Zone.title).first()

    if existing_zone:
        raise HTTPException(status_code=400, detail="Такая зона уже есть")

    new_zone = Zone(title=zone_data.title, description=zone_data.description)

    db.add(new_zone)
    db.commit()
    db.refresh(new_zone)

    return new_zone


@router.put("/{zone_id}", response_model=ZoneResponse, status_code=status.HTTP_200_OK)
def update_zone(
    zone_id: int,
    zone_data: ZoneCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """обновление зоны"""
    zone = db.query(Zone).filter(zone_id == Zone.id).first()

    if not zone:
        raise HTTPException(status_code=404, detail="Зона не найдена")

    zone.title = zone_data.title
    zone.description = zone_data.description

    db.commit()
    db.refresh(zone)

    return zone


@router.delete("/{zone_id}", status_code=status.HTTP_200_OK)
def delete_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """удаление зоны"""
    zone = db.query(Zone).filter(Zone.id == zone_id).first()

    if not zone:
        raise HTTPException(status_code=404, detail="Такой зоны нет")

    db.delete(zone)
    db.commit()

    return {"ok": True, "message": "Зона удалена"}
