from datetime import datetime, timezone
from urllib.parse import urlencode


def certificate_ready(cleared: set[str], slugs: list[str]) -> bool:
    return set(slugs) <= cleared


def format_issued(when: datetime) -> str:
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when.astimezone(timezone.utc).strftime("%d %B %Y")


def linkedin_url(base: str, public_id: str, language_name: str, issued: datetime) -> str:
    when = issued if issued.tzinfo else issued.replace(tzinfo=timezone.utc)
    verify = f"{base.rstrip('/')}/verify/{public_id}"
    params = {
        "startTask": "CERTIFICATION_NAME",
        "name": f"DSA Gaming Engine {language_name}",
        "organizationName": "DSA Gaming Engine",
        "issueYear": str(when.year),
        "issueMonth": str(when.month),
        "certUrl": verify,
        "certId": public_id,
    }
    return "https://www.linkedin.com/profile/add?" + urlencode(params)
