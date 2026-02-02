from base64 import decode

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.schemas.user import UserLogin, UserCreate, UserResponse
from app.schemas.token import RefreshRequest, TokenResponse
from app.models import User
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.utils.dependencies import get_current_user
from datetime import timedelta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя
    
    - Email должен быть уникальным
    - Пароль будет захеширован (Argon2)
    """

    # проверка на наличие пользователя в базе
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(f"Registration attempt with existing email: {user_data.email}")
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
    
    logger.info(f"User registered: {new_user.email} (ID={new_user.id})")

    return new_user

@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)) -> dict:
    """Вход пользователя (выдача JWT tokens)
    
    Возвращает access_token (30 мин) и refresh_token (7 дней)
    """

    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        logger.warning(f"Login attempt with non-existent email: {user_data.email}")
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    # проверка пароля
    if not verify_password(user_data.password, user.password):
        logger.warning(f"Login attempt with wrong password for email: {user_data.email}")
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    # создание токена
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email, "is_admin": user.is_admin}, expires_delta=timedelta(minutes=30)
    )

    refresh_token = create_refresh_token(
        data={"user_id": user.id}
    )
    
    logger.info(f"User logged in: {user.email} (ID={user.id})")

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Получить профиль текущего пользователя"""
    return current_user


@router.post("/refresh")
def refresh_access_token(request: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    """Обновить access_token с помощью refresh_token
    
    Refresh token действует 7 дней, access token перевыпускается на 30 минут
    """

    # расшифровка refresh token
    payload = decode_token(request.refresh_token)

    if payload is None:
        logger.warning("Invalid or expired refresh token used")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный или истёкший refresh token")

    # проверка, что это именно refresh
    if payload.get("type") != "refresh":
        logger.warning("Non-refresh token used for refresh endpoint")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Это не refresh token")

    # получаем user_id
    user_id = payload.get("user_id")

    if not user_id:
        logger.warning("Refresh token without user_id")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Некоррекнтый токен")

    # находим пользователя в бд
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"Refresh token for non-existent user: {user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    # создание нового access_token
    new_access_token = create_access_token(
        data={"user_id": user.id,
              "email": user.email,
              "is_admin": user.is_admin},
              expires_delta=timedelta(minutes=30)
    )
    
    logger.info(f"Access token refreshed for user: {user.email} (ID={user.id})")

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
