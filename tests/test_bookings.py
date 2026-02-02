from app.models import Table, Booking, User
from datetime import datetime, timedelta


def register_and_get_token(client, email, password, fullname="User"):
    r = client.post("/auth/register", json={
        "email": email,
        "password": password,
        "fullname": fullname,
        "phone": "+70000000000"
    })
    assert r.status_code == 201
    user_id = r.json()["id"]

    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"], user_id


def test_booking_create_and_conflict(client, db_session):
    # create admin and zone/table
    admin_token, admin_id = register_and_get_token(client, "admin2@example.com", "adminpass")
    admin = db_session.query(User).filter(User.id == admin_id).first()
    admin.is_admin = True
    db_session.add(admin)
    db_session.commit()
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    # create zone
    r = client.post("/zones/", json={"title": "ZoneA", "description": ""}, headers=headers_admin)
    assert r.status_code == 201
    zone_id = r.json()["id"]

    # create table
    r = client.post("/tables/", json={"number": 10, "count_place": 4, "zone_id": zone_id}, headers=headers_admin)
    assert r.status_code == 201
    table_id = r.json()["id"]

    # register two users
    token_a, user_a = register_and_get_token(client, "a@example.com", "passA")
    token_b, user_b = register_and_get_token(client, "b@example.com", "passB")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # user A books table for a timeslot
    now = datetime.utcnow()
    start = (now + timedelta(hours=1)).isoformat()
    stop = (now + timedelta(hours=2)).isoformat()

    r = client.post("/bookings/", json={"table_id": table_id, "count_people": 2, "time_start": start, "time_stop": stop}, headers=headers_a)
    assert r.status_code == 201, r.text

    # user B tries to book overlapping timeslot -> should fail
    overlap_start = (now + timedelta(hours=1, minutes=30)).isoformat()
    overlap_stop = (now + timedelta(hours=2, minutes=30)).isoformat()
    r = client.post("/bookings/", json={"table_id": table_id, "count_people": 2, "time_start": overlap_start, "time_stop": overlap_stop}, headers=headers_b)
    assert r.status_code == 400

    # user B books non-overlapping timeslot -> should succeed
    non_overlap_start = (now + timedelta(hours=2, minutes=30)).isoformat()
    non_overlap_stop = (now + timedelta(hours=3, minutes=30)).isoformat()
    r = client.post("/bookings/", json={"table_id": table_id, "count_people": 2, "time_start": non_overlap_start, "time_stop": non_overlap_stop}, headers=headers_b)
    assert r.status_code == 201


def test_get_available_tables(client, db_session):
    # create admin and zone/table
    admin_token, admin_id = register_and_get_token(client, "admin3@example.com", "adminpass")
    admin = db_session.query(User).filter(User.id == admin_id).first()
    admin.is_admin = True
    db_session.add(admin)
    db_session.commit()
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    r = client.post("/zones/", json={"title": "ZoneB", "description": ""}, headers=headers_admin)
    assert r.status_code == 201
    zone_id = r.json()["id"]

    r = client.post("/tables/", json={"number": 20, "count_place": 4, "zone_id": zone_id}, headers=headers_admin)
    assert r.status_code == 201
    table_id = r.json()["id"]

    # create a booking that occupies a slot
    user_token, user_id = register_and_get_token(client, "userC@example.com", "passC")
    headers_user = {"Authorization": f"Bearer {user_token}"}

    today = datetime.utcnow().date()
    time_start = "10:00"
    time_stop = "12:00"
    date_str = today.strftime("%Y-%m-%d")

    # create booking via /bookings/ with appropriate datetimes
    start_dt = datetime.combine(today, datetime.strptime("10:00", "%H:%M").time()).isoformat()
    stop_dt = datetime.combine(today, datetime.strptime("12:00", "%H:%M").time()).isoformat()
    r = client.post("/bookings/", json={"table_id": table_id, "count_people": 2, "time_start": start_dt, "time_stop": stop_dt}, headers=headers_user)
    assert r.status_code == 201

    # request available tables for overlapping time -> should not include this table
    r = client.get(f"/tables/available?date={date_str}&time_start=11:00&time_stop=11:30", headers={})
    assert r.status_code == 200
    tables = r.json()
    assert isinstance(tables, list)
    # table should be absent
    assert all(t["id"] != table_id for t in tables)

    # request available tables for non-overlapping time -> should include table
    r = client.get(f"/tables/available?date={date_str}&time_start=12:30&time_stop=13:30", headers={})
    assert r.status_code == 200
    tables = r.json()
    assert any(t["id"] == table_id for t in tables)
