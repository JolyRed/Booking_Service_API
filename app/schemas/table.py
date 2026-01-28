from pydantic import BaseModel
from datetime import datetime

class TableCreate(BaseModel):
    number: int
    count_place: int
    zone_id: int

class TableResponse(BaseModel):
    id: int
    number: int
    count_place: int
    zone_id: int
    created_at: datetime

    class Config:
        from_attributes = True