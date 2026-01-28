from sqlalchemy import Column, Integer, ForeignKey, func, DateTime
from app.database import Base

class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, nullable=False)
    count_place = Column(Integer, nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
