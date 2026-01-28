from sqlalchemy import Column, Integer, String, ForeignKey, func, DateTime
from app.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    count_people = Column(Integer, nullable=False)
    time_start = Column(DateTime, nullable=False)
    time_stop = Column(DateTime, nullable=False)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, server_default=func.now())