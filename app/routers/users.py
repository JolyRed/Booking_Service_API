from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.models import User
from app.utils.dependencies import get_current_admin


router = APIRouter(prefix="/users", tags=["Users"])

# назначение админстратора(только для админов)
@router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def make_admin(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    user = db.query(User).filter(user_id == User.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user.is_admin = True

    db.commit()
    db.refresh(user)

    return user

@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def user_blocking(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    user = db.query(User).filter(user_id == User.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user.is_blocked = True

    db.commit()
    db.refresh(user)

    return user

@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def user_unblocking(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    user = db.query(User).filter(user_id == User.id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user.is_blocked = False

    db.commit()
    db.refresh(user)

    return user
