"""Reusable crypto helpers for Module 18.

Small, dependency-light demonstrations of the primitives that auth (Module 19) is
built on. NOT a production crypto library — use `passlib`, `pyjwt`, and the
`cryptography` package for real systems. These exist to make the ideas concrete.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json


def b64url_encode(raw: bytes) -> str:
    """URL-safe base64 WITHOUT padding — exactly how JWT encodes its parts."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def b64url_decode(data: str) -> bytes:
    """Inverse of b64url_encode — re-add the stripped '=' padding."""
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def sign_hs256(message: bytes, secret: bytes) -> bytes:
    """HMAC-SHA256 signature — the 'HS256' in a JWT header."""
    return hmac.new(secret, message, hashlib.sha256).digest()


def constant_time_equal(a: bytes, b: bytes) -> bool:
    """Compare without leaking *where* two values differ via timing.

    `a == b` can short-circuit on the first differing byte; an attacker measures
    the time to learn the secret byte by byte. hmac.compare_digest does not.
    """
    return hmac.compare_digest(a, b)


def make_jwt_hs256(payload: dict, secret: str) -> str:
    """Build a JWT by hand: base64url(header).base64url(payload).base64url(sig)."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = sign_hs256(signing_input, secret.encode())
    return f"{header_b64}.{payload_b64}.{b64url_encode(signature)}"


def verify_jwt_hs256(token: str, secret: str) -> dict:
    """Verify signature and return the payload, or raise ValueError.

    The whole security model: re-sign the header.payload with the secret and
    compare (constant-time) to the signature the token carries. A tampered
    payload changes the signing input, so the signatures will not match.
    """
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError as exc:
        raise ValueError("Malformed token: expected three dot-separated parts") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected = sign_hs256(signing_input, secret.encode())
    provided = b64url_decode(sig_b64)

    if not constant_time_equal(expected, provided):
        raise ValueError("Invalid signature — token was tampered with or wrong secret")

    return json.loads(b64url_decode(payload_b64))
