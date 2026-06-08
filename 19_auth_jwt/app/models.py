"""User model — stores the password HASH, never the password itself."""
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    # The bcrypt hash, e.g. "$2b$12$...". The plaintext password is never stored.
    hashed_password: Mapped[str] = mapped_column(String(128))
