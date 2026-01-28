from app.routers import auth, bookings, tables
from fastapi import FastAPI

app = FastAPI(title="Booking Service API")

app.include_router(auth.router)
app.include_router(bookings.router)
app.include_router(tables.router)

@app.get("/")
def root():
    return {"message": "Booking Service API is running!"}
