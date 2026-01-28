from datetime import datetime
from pydantic import BaseModel

class BookingCreate(BaseModel):
    table_id: int
    count_people: int
    time_start: datetime
    time_stop: datetime

class BookingResponse(BaseModel):
    id: int
    table_id: int
    user_id: int
    count_people: int
    time_start: datetime
    time_stop: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class BookingUpdate(BaseModel):
    status: str