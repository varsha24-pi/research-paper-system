import sys
import os
import uuid

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import engine, Base

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_auth_pipeline():
    print("=" * 65)
    print(" Running User Authentication & JWT Tests")
    print("=" * 65)

    unique_suffix = uuid.uuid4().hex[:6]
    test_username = f"researcher_{unique_suffix}"
    test_email = f"researcher_{unique_suffix}@university.edu"
    test_password = "SecurePassword@123"
    test_fullname = "Dr. Jane Doe"

    # 1. Test User Registration
    reg_payload = {
        "username": test_username,
        "email": test_email,
        "password": test_password,
        "full_name": test_fullname
    }
    reg_res = client.post("/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    reg_data = reg_res.json()
    assert reg_data["username"] == test_username
    assert reg_data["email"] == test_email
    assert "password" not in reg_data  # Password hash is never exposed
    print(f"[PASS] User registered successfully: ID #{reg_data['id']} ({test_username})")

    # 2. Test Duplicate Registration Prevention
    dup_res = client.post("/auth/register", json=reg_payload)
    assert dup_res.status_code == 400, "Should reject duplicate username/email"
    print(f"[PASS] Duplicate registration rejected with HTTP 400.")

    # 3. Test Login with Incorrect Password
    wrong_login = client.post("/auth/login", json={"username": test_username, "password": "WrongPassword"})
    assert wrong_login.status_code == 401, "Should reject invalid credentials"
    print(f"[PASS] Invalid password rejected with HTTP 401 Unauthorized.")

    # 4. Test Successful Login (Get JWT Token)
    login_res = client.post("/auth/login", json={"username": test_username, "password": test_password})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    access_token = token_data["access_token"]
    print(f"[PASS] User login successful. Received JWT token: {access_token[:20]}...")

    # 5. Test Protected /auth/me without Token -> 401
    unauth_me = client.get("/auth/me")
    assert unauth_me.status_code == 401
    print(f"[PASS] Access to /auth/me without token rejected with HTTP 401.")

    # 6. Test Protected /auth/me with Bearer Token -> 200
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    auth_me = client.get("/auth/me", headers=auth_headers)
    assert auth_me.status_code == 200
    assert auth_me.json()["username"] == test_username
    print(f"[PASS] Access to /auth/me with JWT token successful: {auth_me.json()['full_name']}")

    # 7. Test User-Specific Documents Endpoint /documents/user/my-papers
    my_papers_res = client.get("/documents/user/my-papers", headers=auth_headers)
    assert my_papers_res.status_code == 200
    assert my_papers_res.json()["user_id"] == reg_data["id"]
    print(f"[PASS] User-specific documents endpoint /documents/user/my-papers verified.")

    print("=" * 65)
    print("[OK] All Authentication & JWT Tests Passed Successfully!")
    print("=" * 65)


if __name__ == "__main__":
    test_auth_pipeline()
