from datetime import datetime

from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin
from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash


class AdminUser(UUIDMixin, TimestampMixin, db.Model):
    __tablename__ = "admin_user"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(160))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self) -> str:
        return f"<AdminUser {self.email}>"


class TokenBlocklist(UUIDMixin, db.Model):
    """Revoked JWTs, checked on every protected request."""

    __tablename__ = "token_blocklist"

    jti: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, index=True
    )
    token_type: Mapped[str] = mapped_column(String(16), nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
