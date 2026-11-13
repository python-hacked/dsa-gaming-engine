import secrets

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dsa_gaming.modules.catalog.data import DSA_GAMES, LANGUAGE_IDS, LANGUAGES
from dsa_gaming.modules.certificates.models import Certificate, CertificateSignature
from dsa_gaming.modules.certificates.service import certificate_ready, format_issued, linkedin_url
from dsa_gaming.modules.gameplay.models import GameAttempt, MarathonRun
from dsa_gaming.modules.identity.models import User, utcnow


def _language(code: str | None) -> str:
    if code in LANGUAGE_IDS:
        return code
    return "python"


async def list_certificates(session: AsyncSession, user_id: int) -> list[Certificate]:
    result = await session.execute(
        select(Certificate).where(Certificate.user_id == user_id).order_by(Certificate.issued_at, Certificate.id)
    )
    return list(result.scalars().all())


async def certificate_by_public_id(session: AsyncSession, public_id: str) -> tuple[Certificate, User] | None:
    result = await session.execute(
        select(Certificate, User).join(User, User.id == Certificate.user_id).where(Certificate.public_id == public_id)
    )
    row = result.first()
    if row is None:
        return None
    return row[0], row[1]


async def issued_language_map(session: AsyncSession, user_ids: list[int]) -> dict[int, list[str]]:
    if not user_ids:
        return {}
    result = await session.execute(select(Certificate).where(Certificate.user_id.in_(user_ids)))
    found: dict[int, list[str]] = {}
    for row in result.scalars():
        found.setdefault(row.user_id, []).append(row.language)
    return found


async def languages_cleared_in_one_sitting(session: AsyncSession, user_id: int) -> set[str]:
    slugs = {game["slug"] for game in DSA_GAMES}
    result = await session.execute(
        select(MarathonRun.id, MarathonRun.language, GameAttempt.slug)
        .join(GameAttempt, GameAttempt.run_id == MarathonRun.id)
        .where(MarathonRun.user_id == user_id, GameAttempt.passed.is_(True))
    )
    cleared: dict[int, set[str]] = {}
    language_of: dict[int, str] = {}
    for run_id, language, slug in result.all():
        cleared.setdefault(run_id, set()).add(slug)
        language_of[run_id] = language
    return {language_of[run_id] for run_id, got in cleared.items() if certificate_ready(got, list(slugs))}


async def run_languages(session: AsyncSession, user_id: int) -> list[str]:
    result = await session.execute(
        select(MarathonRun.language).where(MarathonRun.user_id == user_id).distinct()
    )
    return [code for code in result.scalars().all() if code in LANGUAGE_IDS]


async def issue_certificate(session: AsyncSession, user_id: int, language: str | None) -> Certificate | None:
    user = await session.get(User, user_id)
    if user is None:
        return None
    code = _language(language)
    existing = (
        await session.execute(
            select(Certificate).where(Certificate.user_id == user_id, Certificate.language == code)
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    now = utcnow()
    row = Certificate(public_id=secrets.token_hex(8), user_id=user_id, language=code, issued_at=now)
    user.certificate_unlocked = True
    if user.certificate_unlocked_at is None:
        user.certificate_unlocked_at = now
    session.add(row)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        again = (
            await session.execute(
                select(Certificate).where(Certificate.user_id == user_id, Certificate.language == code)
            )
        ).scalar_one_or_none()
        return again
    await session.refresh(row)
    return row


async def sync_earned_certificates(session: AsyncSession, user: User) -> None:
    for language in await languages_cleared_in_one_sitting(session, user.id):
        await issue_certificate(session, user.id, language)
    if user.certificate_unlocked and not await list_certificates(session, user.id):
        await issue_certificate(session, user.id, user.active_language)


def _display(code: str) -> str:
    for language_id, name in LANGUAGES:
        if language_id == code:
            return name
    return code


async def certificate_cards(session: AsyncSession, user: User, base_url: str) -> list[dict]:
    await sync_earned_certificates(session, user)
    rows = await list_certificates(session, user.id)
    by_language = {row.language: row for row in rows}
    order = [row.language for row in rows]
    for code in await run_languages(session, user.id):
        if code not in by_language and code not in order:
            order.append(code)
    focus = user.active_language if user.active_language in LANGUAGE_IDS else "python"
    if focus not in order:
        order.append(focus)
    cards = []
    for code in order:
        name = _display(code)
        row = by_language.get(code)
        if row is None:
            cards.append(
                {
                    "language": code,
                    "language_name": name,
                    "ready": False,
                    "issued_on": "",
                    "public_id": "",
                    "download_href": "",
                    "share_href": "",
                    "open_href": "",
                }
            )
            continue
        cards.append(
            {
                "language": code,
                "language_name": name,
                "ready": True,
                "issued_on": format_issued(row.issued_at),
                "public_id": row.public_id,
                "download_href": f"/app/certificate/{row.public_id}/download",
                "share_href": linkedin_url(base_url, row.public_id, name, row.issued_at),
                "open_href": f"/app/certificate/{row.public_id}",
            }
        )
    return cards


async def get_signature(session: AsyncSession) -> CertificateSignature | None:
    result = await session.execute(select(CertificateSignature).order_by(CertificateSignature.id.desc()))
    return result.scalars().first()


async def save_signature(session: AsyncSession, signer_name: str, image: bytes) -> CertificateSignature:
    await session.execute(delete(CertificateSignature))
    row = CertificateSignature(
        signer_name=signer_name[:200],
        image=image,
        content_type="image/png",
        updated_at=utcnow(),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row
