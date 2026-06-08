# Auth API — JWT + password security

Register, log in for a JWT, and call a protected route. Backs the Module 19 notebook.

## Run

```bash
cd 19_auth_jwt
uvicorn app.main:app --reload
```

Interactive docs at http://127.0.0.1:8000/docs — the "Authorize" button there
runs the whole flow for you.

## Flow (curl)

```bash
# 1. register
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "supersecret1"}'

# 2. get a token (note: form-encoded, not JSON — OAuth2 password flow)
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/token \
  -d "username=alice&password=supersecret1" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. call the protected route with the Bearer token
curl http://127.0.0.1:8000/me -H "Authorization: Bearer $TOKEN"

# without a token -> 401
curl -i http://127.0.0.1:8000/me
```

## Layout

| File | Role |
|------|------|
| `auth.py` | password hashing (bcrypt) + JWT create/decode (pyjwt) |
| `models.py` | `User` table (stores `hashed_password`, never plaintext) |
| `schemas.py` | request/response contracts (`UserCreate`, `Token`, ...) |
| `main.py` | `/register`, `/token`, protected `/me`, `get_current_user` dependency |

Set `JWT_SECRET` in the environment for anything beyond local play.
