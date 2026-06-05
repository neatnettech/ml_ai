"""Auth core: password hashing + JWT create/decode.

Built on the primitives from Module 18 — but using the production libraries
(`passlib` for bcrypt, `pyjwt` for tokens) instead of hand-rolled crypto.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt  # pyjwt

# In production, load this from a secret manager / env var and NEVER commit it.
SECRET_KEY = os.getenv("JWT_SECRET", "dev-only-secret-change-me-in-production-32b")
ALGORITHM = "HS256"  # HMAC-SHA256 — the signature from Module 18, Step 6
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    """bcrypt: deliberately slow + salted. The salt is generated and stored
    inside the returned hash string, so you never manage salts yourself.

    bcrypt only uses the first 72 bytes of the password; schemas cap input length.
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(subject: str, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    """Build a signed JWT. `sub` is who the token is for; `exp` when it dies."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Verify signature + expiry, return the subject (username).

    Raises jwt.PyJWTError (InvalidSignatureError, ExpiredSignatureError, ...) on
    any problem — the caller turns that into a 401.
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    subject = payload.get("sub")
    if subject is None:
        raise jwt.InvalidTokenError("Token missing 'sub' claim")
    return subject
