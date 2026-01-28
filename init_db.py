from app.database import engine, Base
from app.models import User, Zone, Table, Booking

def init_db():
    print("Создание таблиц...")
    Base.metadata.create_all(engine)
    print("Таблицы созданы!!!")

if __name__ == "__main__":
    init_db()
