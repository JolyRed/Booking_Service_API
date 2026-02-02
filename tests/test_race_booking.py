import threading
from datetime import datetime, timedelta
import pytest

from app.utils.security import create_access_token, hash_password
from app.models import User, Zone, Table, Booking
from tests.conftest import TestingSessionLocal, engine


def test_concurrent_booking_requests(concurrent_client):
    # SQLite doesn't support reliable row-level locking; skip this test when using sqlite.
    if engine.dialect.name == 'sqlite':
        pytest.skip("Race-condition test skipped on SQLite; run on Postgres for accurate locking")

    """Simulate two concurrent booking requests for the same table/time.

    Expectation: only one booking is created, the other request fails with 400.
    This test exercises the critical section in the booking creation
    route (row locking / conflict detection).
    """

    # prepare DB objects in a fresh session and commit so other sessions can see them
    setup_session = TestingSessionLocal()
    try:
        zone = Zone(title="Main Hall")
        setup_session.add(zone)
        setup_session.commit()
        setup_session.refresh(zone)

        table = Table(number=1, count_place=4, zone_id=zone.id)
        setup_session.add(table)
        setup_session.commit()
        setup_session.refresh(table)

        user = User(email="race@test.local", password=hash_password("secret"), fullname="Race User")
        setup_session.add(user)
        setup_session.commit()
        setup_session.refresh(user)

        # capture primitive ids before closing session
        zone_id = zone.id
        table_id = table.id
        user_id = user.id
    finally:
        setup_session.close()

    token = create_access_token({"user_id": user_id})

    # booking time window (overlapping)
    ts = datetime.utcnow() + timedelta(hours=1)
    te = ts + timedelta(hours=2)

    payload = {
        "table_id": table_id,
        "count_people": 2,
        "time_start": ts.isoformat(),
        "time_stop": te.isoformat(),
    }

    results = [None, None]

    def worker(idx):
        try:
            res = concurrent_client.post(
                "/bookings/",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
            results[idx] = (res.status_code, res.json() if res.content else None)
        except Exception as e:
            results[idx] = ("exc", str(e))

    threads = [threading.Thread(target=worker, args=(0,)), threading.Thread(target=worker, args=(1,))]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify only one booking recorded in DB (race-condition guard)
    check_session = TestingSessionLocal()
    try:
        count = (
            check_session.query(Booking)
            .filter(Booking.table_id == table.id, Booking.time_start == ts)
            .count()
        )
        assert count == 1
    finally:
        check_session.close()
