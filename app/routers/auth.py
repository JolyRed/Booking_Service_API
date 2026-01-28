from base64 import decode

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserLogin, UserCreate, UserResponse
from app.schemas.token import RefreshRequest, TokenResponse
from app.models import User
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.utils.dependencies import get_current_user
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя
    """

    # проверка на наличие пользователя в базе
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Такой пользователь уже зарегестрирован")

    # хеширование пароля
    hashed_password = hash_password(user_data.password)

    # создание нового пользователя
    new_user = User(
        email=user_data.email,
        password=hashed_password,
        fullname=user_data.fullname,
        phone=user_data.phone,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)) -> dict:
    """ Вход юзера """

    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")


    """
    проверка пароля
    """
    if not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    """
    создание токена
    """

    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email, "is_admin": user.is_admin}, expires_delta=timedelta(minutes=30)
    )

    refresh_token = create_refresh_token(
        data={"user_id": user.id}
    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """ получить текущего пользователя"""
    return current_user


@router.post("/refresh")
def refresh_access_token(request: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    """ обновить access_token с помошью refresh_token"""

    # расшифровка refresh token
    payload = decode_token(request.refresh_token)

    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный или истёкший refresh token")

    # проверка, что это именно refresh
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Это не refresh token")

    # получаем user_id
    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Некоррекнтый токен")

    # находим пользователя в бд

    user = db.query(User).filter(user_id == User.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    # создание нового access_token
    new_access_token = create_access_token(
        data={"user_id": user.id,
              "email": user.email,
              "is_admin": user.is_admin},
              expires_delta=timedelta(minutes=30)
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
