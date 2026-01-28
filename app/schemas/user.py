from pydantic import BaseModel, EmailStr
from datetime import datetime

# Что получаем от пользователя
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    fullname: str
    phone: str

# Что отдаём пользователю
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    fullname: str
    phone: str
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Для регистрации
class UserLogin(BaseModel):
    email: EmailStr
    password: str

