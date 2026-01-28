from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.config import settings
from jose import JWTError, jwt

# объект для работы bcrypt(алгоритм хеширования)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    превращает обычный пароль в хэш
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ Проверяет, совпадает ли пароль с хэшем"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """ Создаёт JWT Token"""
    to_encode = data.copy()

    # устанавливаем время истечения токена
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})

    # создаём токен
    encode_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encode_jwt

def create_refresh_token(data: dict) -> str:
    """ создание refresh токена """
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})

    encode_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    return encode_jwt

def decode_token(token: str) -> dict:
    """Расшифровка токена"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


