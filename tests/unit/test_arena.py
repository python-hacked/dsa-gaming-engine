import json
from base64 import b64encode

import itsdangerous
from fastapi.testclient import TestClient

from dsa_gaming.core.config import get_settings
from dsa_gaming.main import create_app


def _login(client: TestClient, name: str = "Satish") -> None:
    signer = itsdangerous.TimestampSigner(get_settings().session_secret)
    payload = {
        "user": {
            "sub": "test-sub",
            "email": "satish@example.com",
            "name": name,
            "picture": "",
        }
    }
    raw = b64encode(json.dumps(payload).encode("utf-8"))
    client.cookies.set("dsa_session", signer.sign(raw).decode("utf-8"))


def test_home_shows_both_tracks():
    client = TestClient(create_app())
    _login(client)
    page = client.get("/app")
    assert page.status_code == 200
    assert "Satish" in page.text
    assert "20 mind games" in page.text
    assert "20 query tasks" in page.text


def test_dsa_language_lists_games():
    client = TestClient(create_app())
    _login(client)
    response = client.post("/app/dsa/language", data={"language": "python"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Array Swap Sort" in response.text
    assert "Pattern Match" in response.text


def test_sql_track_lists_tasks():
    client = TestClient(create_app())
    _login(client)
    page = client.get("/app/sql")
    assert page.status_code == 200
    assert "Inner Join" in page.text
    assert "Faster Query" in page.text


def test_profile_icon_opens_a_locked_certificate():
    client = TestClient(create_app())
    _login(client)
    home = client.get("/app")
    assert 'href="/app/profile"' in home.text
    page = client.get("/app/profile")
    assert page.status_code == 200
    assert "Satish" in page.text
    assert "cert-sheet" in page.text
    assert "Certificate of completion" in page.text
    assert "Python" in page.text
    assert "Locked" in page.text
    assert "0 of 20" in page.text
    locked = client.get("/app/certificate", follow_redirects=False)
    assert locked.status_code == 303
    assert locked.headers["location"] == "/app/profile"


def test_tracks_are_closed_to_guests():
    client = TestClient(create_app())
    response = client.get("/app/dsa", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
