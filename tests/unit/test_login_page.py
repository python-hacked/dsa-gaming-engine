from fastapi.testclient import TestClient

from dsa_gaming.main import create_app


def test_root_is_google_login():
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    assert "Continue with Google" in response.text
    assert 'href="/auth/google/login"' in response.text
    assert "Admin login" in response.text
    assert 'action="/auth/admin/login"' in response.text


def test_arena_sends_guests_back_to_login():
    client = TestClient(create_app())
    response = client.get("/app", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_google_login_without_keys_returns_to_first_page():
    app = create_app()
    app.state.settings = app.state.settings.model_copy(
        update={"google_client_id": "", "google_client_secret": ""}
    )
    client = TestClient(app)
    response = client.get("/auth/google/login", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/?error=google_not_configured"

    page = client.get("/?error=google_not_configured")
    assert page.status_code == 200
    assert "client id and secret" in page.text
