from pydantic import BaseModel
from datetime import datetime

class ZoneCreate(BaseModel):
    title: str
    description: str


class ZoneResponse(BaseModel):
    id: int
    title: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True