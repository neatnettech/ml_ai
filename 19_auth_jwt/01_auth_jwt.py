# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Module 19 — Authentication: JWT + Password Security
#
# You can build an API (Module 17) and you understand the crypto (Module 18). Now
# combine them into a real **login system** and lock your endpoints down.
#
# You will learn:
#
# 1. **Password hashing with bcrypt** — the production version of Module 18's salting
# 2. **JWTs with `pyjwt`** — issue and verify signed tokens, with expiry
# 3. **OAuth2 password flow** — the standard "log in, get a token" handshake
# 4. **Protected routes** — a `Depends` that rejects anyone without a valid token
#
# The runnable service is in `app/`. This notebook explains it and exercises the
# full flow with `TestClient`.

# %%
import bcrypt
import jwt  # pyjwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.testclient import TestClient
from pydantic import BaseModel

print("Auth stack ready — bcrypt + pyjwt + FastAPI.")

# %% [markdown]
# ## Step 1: Hash passwords with bcrypt
#
# In Module 18 you salted + hashed by hand. In production you use the **bcrypt**
# library: `gensalt()` makes a random salt, `hashpw()` runs a deliberately slow
# algorithm and stores the salt *inside* the hash string, and `checkpw()` verifies.
#
# bcrypt works on bytes, so `.encode()` going in and `.decode()` to store as text.
# (Note: bcrypt only reads the first 72 bytes of a password — cap input length.)

# %%
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


hashed = hash_password("supersecret1")
print("Stored hash:", hashed)
print("(the salt + cost factor are embedded in that string)")

# Same password hashed twice → DIFFERENT strings (random salt each time):
print("\nHash again:", hash_password("supersecret1"))

print("\nVerify correct:", verify_password("supersecret1", hashed))  # True
print("Verify wrong:  ", verify_password("wrongpass", hashed))       # False

# %% [markdown]
# ## Step 2: Issue and verify JWTs with pyjwt
#
# A JWT carries **claims** — at minimum `sub` (subject: who it is for) and `exp`
# (expiry). `pyjwt` signs it with your secret (HS256 = the HMAC from Module 18) and,
# on decode, **verifies the signature and the expiry** for you.

# %%
from datetime import datetime, timedelta, timezone

SECRET_KEY = "dev-only-secret-change-me-in-production-32b"
ALGORITHM = "HS256"


def create_access_token(subject: str, expires_minutes: int = 30) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "iat": now, "exp": now + timedelta(minutes=expires_minutes)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


token = create_access_token("alice")
print("Token:", token)

decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
print("\nDecoded claims:", decoded)
print("Subject (who):", decoded["sub"])

# %% [markdown]
# ### Expiry and tampering are enforced on decode
#
# `jwt.decode` raises if the token expired, was signed with a different key, or was
# altered. You convert those exceptions into a `401`.

# %%
# Expired token:
expired = create_access_token("alice", expires_minutes=-1)  # already in the past
try:
    jwt.decode(expired, SECRET_KEY, algorithms=[ALGORITHM])
except jwt.ExpiredSignatureError:
    print("Expired token rejected (ExpiredSignatureError).")

# Wrong secret (forged):
try:
    jwt.decode(token, "attacker-guessed-key", algorithms=[ALGORITHM])
except jwt.InvalidSignatureError:
    print("Bad-signature token rejected (InvalidSignatureError).")

# %% [markdown]
# ## Step 3: The OAuth2 password flow
#
# The standard handshake:
#
# 1. Client `POST`s `username` + `password` (form-encoded) to `/token`.
# 2. Server verifies them and returns `{"access_token": ..., "token_type": "bearer"}`.
# 3. Client sends `Authorization: Bearer <token>` on every protected request.
#
# FastAPI ships helpers for exactly this: `OAuth2PasswordRequestForm` (reads the
# form) and `OAuth2PasswordBearer` (reads the header). Let's assemble a mini app.

# %%
app = FastAPI(title="Auth API (notebook demo)")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# A toy in-memory "database" of one user (hash computed at import time).
FAKE_USERS = {"alice": {"username": "alice", "hashed_password": hash_password("supersecret1")}}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = FAKE_USERS.get(form.username)
    if user is None or not verify_password(form.password, user["hashed_password"]):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user["username"]))


client = TestClient(app)

# Wrong password -> 401
bad = client.post("/token", data={"username": "alice", "password": "nope"})
print("Bad login ->", bad.status_code)

# Correct -> a token
good = client.post("/token", data={"username": "alice", "password": "supersecret1"})
print("Good login ->", good.status_code, good.json())

# %% [markdown]
# ### Exercise 3.1 — Protect a route with `get_current_user`
#
# A protected endpoint needs a dependency that:
# 1. receives the Bearer token (via `Depends(oauth2_scheme)`),
# 2. decodes + verifies it (`jwt.decode`), raising `401` on any `PyJWTError`,
# 3. returns the user (look the `sub` up in `FAKE_USERS`).
#
# Then add a `GET /me` route that depends on it and returns the current user.

# %%
# TODO: Implement get_current_user(token) and a GET /me route.
#
# def get_current_user(token: str = Depends(oauth2_scheme)):
#     credentials_error = HTTPException(401, "Could not validate credentials",
#                                       headers={"WWW-Authenticate": "Bearer"})
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload.get("sub")
#     except jwt.PyJWTError:
#         raise credentials_error
#     user = FAKE_USERS.get(username)
#     if user is None:
#         raise credentials_error
#     return user
#
# @app.get("/me")
# def read_me(current_user: dict = Depends(get_current_user)):
#     return {"username": current_user["username"]}


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_error = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except jwt.PyJWTError:
        raise credentials_error
    user = FAKE_USERS.get(username)
    if user is None:
        raise credentials_error
    return user


@app.get("/me")
def read_me(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["username"]}


# Full flow end to end:
client = TestClient(app)

# No token -> 401
print("GET /me (no token)   ->", client.get("/me").status_code)

# Log in, then call /me with the Bearer token
tok = client.post("/token", data={"username": "alice", "password": "supersecret1"}).json()["access_token"]
me = client.get("/me", headers={"Authorization": f"Bearer {tok}"})
print("GET /me (with token) ->", me.status_code, me.json())

# %% [markdown]
# ## Step 4: From toy to real
#
# The `app/` folder is the production-shaped version of this notebook:
#
# - users live in a **SQLAlchemy** table (Module 17 pattern), not a dict
# - `/register` hashes the password and stores the `User` row
# - `auth.py` holds `hash_password` / `verify_password` / `create_access_token` /
#   `decode_access_token`
# - `get_current_user` looks the user up in the database
#
# Run it:
#
# ```bash
# cd 19_auth_jwt
# uvicorn app.main:app --reload
# ```
#
# then follow `app/README.md` (register → token → `/me`). The `/docs` "Authorize"
# button drives the whole flow interactively.

# %% [markdown]
# ## Security checklist (what makes this safe)
#
# - **Never store plaintext passwords** — only bcrypt hashes.
# - **Never put secrets in the JWT payload** — it is base64, readable by anyone
#   (Module 18). The token proves *identity*, it does not hide data.
# - **Always set `exp`** — short-lived access tokens limit the blast radius of a leak.
# - **Keep `SECRET_KEY` out of source** — load from env / a secret manager.
# - **Return the same 401** for "no such user" and "wrong password" — do not leak
#   which usernames exist.
#
# **Next:** Module 20 — the capstone. Train an ML model, persist it, and serve
# predictions behind this exact auth layer. The full ML → API journey.
