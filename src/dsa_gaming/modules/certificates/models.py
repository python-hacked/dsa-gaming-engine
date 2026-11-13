from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from dsa_gaming.core.database import Base
from dsa_gaming.modules.identity.models import utcnow


class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = (UniqueConstraint("user_id", "language", name="uq_certificates_user_language"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    language: Mapped[str] = mapped_column(String(32))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CertificateSignature(Base):
    __tablename__ = "certificate_signature"

    id: Mapped[int] = mapped_column(primary_key=True)
    signer_name: Mapped[str] = mapped_column(String(200))
    image: Mapped[bytes] = mapped_column(LargeBinary)
    content_type: Mapped[str] = mapped_column(String(64), default="image/png")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
