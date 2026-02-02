from app.routers import auth, bookings, tables, users, zones
from fastapi import FastAPI
import logging
from app.config import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Booking Service API",
    description="API для управления бронированиями столиков в ресторане",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(bookings.router)
app.include_router(tables.router)
app.include_router(users.router)
app.include_router(zones.router)

@app.get("/")
def root():
    """Health check endpoint"""
    return {"message": "Booking Service API is running!"}

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown")
