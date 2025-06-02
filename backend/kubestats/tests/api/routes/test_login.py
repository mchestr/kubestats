from fastapi.testclient import TestClient
from sqlmodel import Session

from kubestats import crud
from kubestats.core.config import settings
from kubestats.models import UserCreate
from kubestats.tests.utils.utils import random_email, random_lower_string


def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]


def test_get_access_token_incorrect_password(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400


def test_whoami(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    """Test whoami endpoint returns current user information."""
    r = client.get(
        f"{settings.API_V1_STR}/me",
        headers=superuser_token_headers,
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result
    assert result["email"] == settings.FIRST_SUPERUSER
    assert "id" in result
    assert "is_active" in result
    assert "is_superuser" in result
    assert result["is_superuser"] is True


def test_login_access_token_success_normal_user(
    client: TestClient, db: Session
) -> None:
    """Test successful login with regular user credentials."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    crud.create_user(session=db, user_create=user_in)

    login_data = {
        "username": email,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert "token_type" in tokens
    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"]


def test_login_access_token_nonexistent_user(client: TestClient) -> None:
    """Test login with non-existent user email."""
    login_data = {
        "username": random_email(),
        "password": random_lower_string(),
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400
    assert r.json()["detail"] == "Incorrect email or password"


def test_login_access_token_incorrect_email(client: TestClient) -> None:
    """Test login with incorrect email format."""
    login_data = {
        "username": "invalid-email",
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400
    assert r.json()["detail"] == "Incorrect email or password"


def test_login_access_token_empty_username(client: TestClient) -> None:
    """Test login with empty username field."""
    login_data = {
        "username": "",
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400


def test_login_access_token_empty_password(client: TestClient) -> None:
    """Test login with empty password field."""
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400
    assert r.json()["detail"] == "Incorrect email or password"


def test_login_access_token_missing_username(client: TestClient) -> None:
    """Test login without username field."""
    login_data = {
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 422  # Validation error


def test_login_access_token_missing_password(client: TestClient) -> None:
    """Test login without password field."""
    login_data = {
        "username": settings.FIRST_SUPERUSER,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 422  # Validation error


def test_login_access_token_inactive_user(client: TestClient, db: Session) -> None:
    """Test login with inactive user account."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=False)
    crud.create_user(session=db, user_create=user_in)

    login_data = {
        "username": email,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400
    assert r.json()["detail"] == "Incorrect email or password"


def test_whoami_with_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test whoami endpoint with normal user token."""
    r = client.get(
        f"{settings.API_V1_STR}/me",
        headers=normal_user_token_headers,
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result
    assert "id" in result
    assert "is_active" in result
    assert "is_superuser" in result
    assert result["is_superuser"] is False


def test_whoami_without_token(client: TestClient) -> None:
    """Test whoami endpoint without authorization header."""
    r = client.get(f"{settings.API_V1_STR}/me")
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authenticated"


def test_whoami_with_invalid_token(client: TestClient) -> None:
    """Test whoami endpoint with invalid token."""
    headers = {"Authorization": "Bearer invalid-token"}
    r = client.get(
        f"{settings.API_V1_STR}/me",
        headers=headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_whoami_with_malformed_header(client: TestClient) -> None:
    """Test whoami endpoint with malformed authorization header."""
    headers = {"Authorization": "InvalidFormat token"}
    r = client.get(
        f"{settings.API_V1_STR}/me",
        headers=headers,
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authenticated"


def test_whoami_with_empty_token(client: TestClient) -> None:
    """Test whoami endpoint with empty Bearer token."""
    headers = {"Authorization": "Bearer "}
    r = client.get(
        f"{settings.API_V1_STR}/me",
        headers=headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Could not validate credentials"


def test_login_token_can_access_protected_route(
    client: TestClient, db: Session
) -> None:
    """Test that login token can be used to access protected routes."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Login to get token
    login_data = {
        "username": email,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200

    # Use token to access protected route
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    r = client.get(f"{settings.API_V1_STR}/me", headers=headers)
    result = r.json()
    assert r.status_code == 200
    assert result["email"] == email
    assert result["id"] == str(user.id)
