from app.models import Zone, Table, User
from datetime import datetime


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


def test_admin_zone_and_table_crud(client, db_session):
    # register user and promote to admin
    token, user_id = register_and_get_token(client, "admin@example.com", "adminpass", "Admin")
    user = db_session.query(User).filter(User.id == user_id).first()
    user.is_admin = True
    db_session.add(user)
    db_session.commit()

    headers = {"Authorization": f"Bearer {token}"}

    # create a zone
    r = client.post("/zones/", json={"title": "Main Hall", "description": "Center"}, headers=headers)
    assert r.status_code == 201, r.text
    zone = r.json()
    zone_id = zone["id"]

    # create a table in this zone
    r = client.post("/tables/", json={"number": 1, "count_place": 4, "zone_id": zone_id}, headers=headers)
    assert r.status_code == 201, r.text
    table = r.json()
    table_id = table["id"]

    # get all tables
    r = client.get("/tables/", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # update table
    r = client.put(f"/tables/{table_id}/update", json={"number": 2, "count_place": 6, "zone_id": zone_id}, headers=headers)
    assert r.status_code == 201
    updated = r.json()
    assert updated["number"] == 2

    # delete table
    r = client.delete(f"/tables/{table_id}/delete", headers=headers)
    assert r.status_code == 200

    # delete zone
    r = client.delete(f"/zones/{zone_id}", headers=headers)
    assert r.status_code == 200
