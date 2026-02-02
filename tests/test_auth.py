from app.models import User


def test_register_login_and_block(client, db_session):
    payload = {
        "email": "testuser@example.com",
        "password": "secret123",
        "fullname": "Test User",
        "phone": "+70000000000"
    }

    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data.get("email") == payload["email"]
    user_id = data.get("id")
    assert user_id is not None

    # Login
    r = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert r.status_code == 200, r.text
    token = r.json().get("access_token")
    assert token

    # Access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    me = r.json()
    assert me.get("email") == payload["email"]

    # Block user in DB directly
    user = db_session.query(User).filter(User.id == user_id).first()
    assert user is not None
    user.is_blocked = True
    db_session.add(user)
    db_session.commit()

    # Now accessing protected endpoint should be forbidden
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 403
