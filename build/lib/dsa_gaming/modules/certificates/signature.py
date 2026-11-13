import base64
import binascii
import io

from PIL import Image, UnidentifiedImageError

MAX_SIGNATURE_BYTES = 1_500_000


class SignatureError(ValueError):
    pass


def decode_drawn(value: str) -> bytes:
    if not value.startswith("data:image/"):
        raise SignatureError("Draw a signature or upload an image.")
    _header, _, encoded = value.partition(",")
    if not encoded:
        raise SignatureError("Draw a signature or upload an image.")
    try:
        raw = base64.b64decode(encoded, validate=False)
    except binascii.Error as exc:
        raise SignatureError("Draw a signature or upload an image.") from exc
    return raw


def normalize_signature(raw: bytes) -> bytes:
    if not raw or len(raw) > MAX_SIGNATURE_BYTES:
        raise SignatureError("Use a PNG, JPEG, or WebP image under 1.5 MB.")
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except UnidentifiedImageError as exc:
        raise SignatureError("Use a PNG, JPEG, or WebP image.") from exc
    if image.format not in {"PNG", "JPEG", "WEBP"}:
        raise SignatureError("Use a PNG, JPEG, or WebP image.")
    image = image.convert("RGBA")
    image.thumbnail((900, 320))
    out = io.BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()
