import json
from base64 import b64encode

import itsdangerous
from fastapi.testclient import TestClient
from sqlalchemy import delete, or_, select

from dsa_gaming.core.config import get_settings
from dsa_gaming.main import create_app
from dsa_gaming.modules.certificates.models import Certificate, CertificateSignature
from dsa_gaming.modules.identity.models import LoginSession, User
from dsa_gaming.modules.identity.repository import upsert_google_user


def _login(client: TestClient, sub: str, email: str, name: str) -> None:
    signer = itsdangerous.TimestampSigner(get_settings().session_secret)
    payload = {"user": {"sub": sub, "email": email, "name": name, "picture": ""}}
    raw = b64encode(json.dumps(payload).encode("utf-8"))
    client.cookies.set("dsa_session", signer.sign(raw).decode("utf-8"))


TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753"
    "de0000000c4944415408d763f8cfc000000301010018dd8db40000000049454e44ae426082"
)


async def _wipe(app, emails: list[str], subs: list[str]) -> None:
    factory = app.state.sessionmaker
    if factory is None:
        return
    async with factory() as db:
        await db.execute(delete(CertificateSignature).where(CertificateSignature.signer_name == "Test Founder"))
        rows = (
            await db.execute(select(User).where(or_(User.email.in_(emails), User.google_sub.in_(subs))))
        ).scalars().all()
        ids = [row.id for row in rows]
        if ids:
            await db.execute(delete(LoginSession).where(LoginSession.user_id.in_(ids)))
            await db.execute(delete(Certificate).where(Certificate.user_id.in_(ids)))
            await db.execute(delete(User).where(User.id.in_(ids)))
        await db.commit()


def test_admin_signup_is_closed_without_a_secret():
    app = create_app()
    app.state.settings = app.state.settings.model_copy(update={"admin_signup_secret": ""})
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/signup",
            json={"name": "Ada", "email": "closed@example.com", "password": "correct-horse", "secret": "anything"},
        )
    assert response.status_code == 503


def test_admin_signup_login_and_certificate_unlock():
    app = create_app()
    app.state.settings = app.state.settings.model_copy(update={"admin_signup_secret": "test-secret"})
    email = "admin-test@example.com"
    player_email = "preview-player-admin-test@example.com"
    player_sub = "admin-test-player"
    with TestClient(app) as client:
        try:
            assert app.state.sessionmaker is not None
            refused = client.post(
                "/api/admin/signup",
                json={"name": "Ada", "email": email, "password": "correct-horse", "secret": "nope"},
            )
            assert refused.status_code == 401
            short = client.post(
                "/api/admin/signup",
                json={"name": "Ada", "email": email, "password": "short", "secret": "test-secret"},
            )
            assert short.status_code == 422
            created = client.post(
                "/api/admin/signup",
                json={"name": "Ada", "email": email, "password": "correct-horse", "secret": "test-secret"},
            )
            assert created.status_code == 201
            assert created.json()["role"] == "admin"
            again = client.post(
                "/api/admin/signup",
                json={"name": "Ada", "email": email, "password": "correct-horse", "secret": "test-secret"},
            )
            assert again.status_code == 409

            bad = client.post(
                "/auth/admin/login",
                data={"email": email, "password": "wrong-password"},
                follow_redirects=False,
            )
            assert bad.status_code == 303
            assert bad.headers["location"] == "/?error=admin_failed"
            failed = client.get("/?error=admin_failed")
            assert "email or password" in failed.text
            assert 'class="admin-login" open' in failed.text

            async def _seed() -> int:
                async with app.state.sessionmaker() as db:
                    user = await upsert_google_user(
                        db,
                        google_sub=player_sub,
                        email=player_email,
                        name="Preview Player",
                        picture="",
                    )
                    return user.id

            player_id = client.portal.call(_seed)
            _login(client, "test-sub", "satish@example.com", "Satish")
            blocked = client.post(
                f"/app/admin/users/{player_id}/certificate",
                follow_redirects=False,
            )
            assert blocked.status_code == 303
            assert blocked.headers["location"] == "/app"

            client.cookies.clear()
            signed = client.post(
                "/auth/admin/login",
                data={"email": email, "password": "correct-horse"},
                follow_redirects=False,
            )
            assert signed.status_code == 303
            assert signed.headers["location"] == "/app/admin"
            home = client.get("/app/admin")
            assert home.status_code == 200
            assert "Preview Player" in home.text
            assert "Time logged in" in home.text
            assert "Unlock certificate" in home.text
            assert "Online now" in home.text

            opened = client.post(
                f"/app/admin/users/{player_id}/certificate",
                follow_redirects=False,
            )
            assert opened.status_code == 303
            assert opened.headers["location"] == "/app/admin"
            listed = client.get("/app/admin")
            assert "Certificate unlocked" in listed.text
            saved = client.post(
                "/app/admin/signature",
                data={"signer_name": "Test Founder"},
                files={"upload": ("sign.png", TINY_PNG, "image/png")},
                follow_redirects=False,
            )
            assert saved.status_code == 303
            assert saved.headers["location"] == "/app/admin?notice=saved"
            image = client.get("/signature")
            assert image.status_code == 200
            assert image.headers["content-type"].startswith("image/png")
            replaced = client.post(
                "/app/admin/signature",
                data={"signer_name": "Test Founder", "drawn": "data:image/png;base64," + b64encode(TINY_PNG).decode()},
                follow_redirects=False,
            )
            assert replaced.status_code == 303
            assert replaced.headers["location"] == "/app/admin?notice=saved"

            client.cookies.clear()
            _login(client, player_sub, player_email, "Preview Player")
            profile = client.get("/app/profile")
            assert profile.status_code == 200
            assert "cert-lock" not in profile.text
            assert "Download" in profile.text
            assert "Share on LinkedIn" in profile.text
            assert "linkedin.com/profile/add" in profile.text
            assert "Python" in profile.text
            assert "Certificate of completion" in profile.text
            assert "Founder &amp; CEO" in profile.text
            assert "Test Founder" in profile.text
            assert 'src="/signature"' in profile.text
            import re
            from datetime import datetime, timezone

            assert datetime.now(timezone.utc).strftime("%d %B %Y") in profile.text
            match = re.search(r'href="(/app/certificate/[^"]+/download)"', profile.text)
            assert match
            pdf = client.get(match.group(1))
            assert pdf.status_code == 200
            assert pdf.headers["content-type"].startswith("application/pdf")
            assert pdf.content.startswith(b"%PDF")
            certificate = client.get("/app/certificate")
            assert certificate.status_code == 200
            assert "Download" in certificate.text
            assert "Share on LinkedIn" in certificate.text
        finally:
            client.portal.call(_wipe, app, [email, player_email], [player_sub])
