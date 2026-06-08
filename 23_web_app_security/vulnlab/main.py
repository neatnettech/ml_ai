"""vulnlab FastAPI app — deliberately insecure endpoints.

⚠️  INTENTIONALLY VULNERABLE. Run on 127.0.0.1 ONLY. Never deploy or expose. ⚠️

Run it (from the repo root or 23_web_app_security/):
    uvicorn vulnlab.main:app --host 127.0.0.1 --port 8000 --reload

Interactive docs: http://127.0.0.1:8000/docs

Vulnerability map (the modules exploit these in order):
    POST /login        — SQL injection (auth bypass), plaintext passwords, no rate limit
    GET  /search       — SQL injection (UNION data exfiltration)
    GET  /notes/{id}   — IDOR / broken access control (no ownership check)
    GET  /profile/{id} — IDOR (leaks api_token of any user)
    GET  /greet        — reflected XSS (unescaped HTML)
    POST /comments     — stored XSS (saved, later rendered unescaped)
    GET  /comments     — renders stored comments unescaped
    GET  /fetch        — SSRF (server fetches an attacker-supplied URL)
    POST /ping         — OS command injection (shells out with the raw host string)
"""
from __future__ import annotations

import os
import subprocess
import urllib.request

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .database import connect, init_db

app = FastAPI(title="vulnlab (INTENTIONALLY VULNERABLE)", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    init_db(reset=True)


# --------------------------------------------------------------------------- #
# Request bodies
# --------------------------------------------------------------------------- #
class LoginIn(BaseModel):
    username: str
    password: str


class CommentIn(BaseModel):
    author: str
    body: str


class PingIn(BaseModel):
    host: str


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "warning": "intentionally vulnerable — localhost only"}


# --------------------------------------------------------------------------- #
# VULN 1 — SQL injection in login (auth bypass) + plaintext passwords
# --------------------------------------------------------------------------- #
@app.post("/login")
def login(data: LoginIn) -> dict[str, str]:
    # VULNERABLE: user input is concatenated straight into the SQL string.
    # Try password:  ' OR '1'='1   to bypass authentication entirely.
    query = (
        "SELECT username, role, api_token FROM users "
        f"WHERE username = '{data.username}' AND password = '{data.password}'"
    )
    conn = connect()
    try:
        row = conn.execute(query).fetchone()
    except Exception as exc:  # leaking the DB error is itself a small vuln
        raise HTTPException(400, detail=f"query error: {exc}")
    finally:
        conn.close()

    if row is None:
        raise HTTPException(401, detail="invalid credentials")
    # The "token" is just the username — trivially forgeable (broken auth, used by IDOR).
    return {"token": row["username"], "role": row["role"]}


# --------------------------------------------------------------------------- #
# VULN 2 — SQL injection in search (UNION exfiltration)
# --------------------------------------------------------------------------- #
@app.get("/search")
def search(q: str) -> dict:
    # VULNERABLE: q is interpolated into the query. A UNION SELECT can pull rows
    # from OTHER tables (e.g. users.password) into the notes result.
    query = f"SELECT id, owner, title FROM notes WHERE title LIKE '%{q}%'"
    conn = connect()
    try:
        rows = [dict(r) for r in conn.execute(query).fetchall()]
    except Exception as exc:
        raise HTTPException(400, detail=f"query error: {exc}")
    finally:
        conn.close()
    return {"query": query, "results": rows}


# --------------------------------------------------------------------------- #
# VULN 3 — IDOR: any note by id, no ownership check
# --------------------------------------------------------------------------- #
@app.get("/notes/{note_id}")
def get_note(note_id: int, x_token: str | None = Header(default=None)) -> dict:
    # VULNERABLE: we never check that x_token (the "logged-in" user) owns this note,
    # nor that a private note belongs to them. Sequential ids make enumeration easy.
    conn = connect()
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(404, detail="not found")
    return dict(row)


# --------------------------------------------------------------------------- #
# VULN 4 — IDOR: profile leaks api_token of any user
# --------------------------------------------------------------------------- #
@app.get("/profile/{user_id}")
def get_profile(user_id: int) -> dict:
    # VULNERABLE: returns the secret api_token; no authz, sequential ids.
    conn = connect()
    row = conn.execute(
        "SELECT id, username, role, api_token FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(404, detail="not found")
    return dict(row)


# --------------------------------------------------------------------------- #
# VULN 5 — reflected XSS
# --------------------------------------------------------------------------- #
@app.get("/greet", response_class=HTMLResponse)
def greet(name: str = "stranger") -> str:
    # VULNERABLE: name is dropped into HTML without escaping.
    # Try:  /greet?name=<script>alert(1)</script>
    return f"<html><body><h1>Hello, {name}!</h1></body></html>"


# --------------------------------------------------------------------------- #
# VULN 6 — stored XSS
# --------------------------------------------------------------------------- #
@app.post("/comments")
def add_comment(data: CommentIn) -> dict[str, str]:
    conn = connect()
    conn.execute(
        "INSERT INTO comments (author, body) VALUES (?, ?)", (data.author, data.body)
    )
    conn.commit()
    conn.close()
    return {"status": "stored"}


@app.get("/comments", response_class=HTMLResponse)
def list_comments() -> str:
    # VULNERABLE: stored comment bodies are rendered unescaped → stored XSS fires
    # for every visitor.
    conn = connect()
    rows = conn.execute("SELECT author, body FROM comments ORDER BY id").fetchall()
    conn.close()
    items = "".join(f"<li><b>{r['author']}</b>: {r['body']}</li>" for r in rows)
    return f"<html><body><h1>Comments</h1><ul>{items}</ul></body></html>"


# --------------------------------------------------------------------------- #
# VULN 7 — SSRF
# --------------------------------------------------------------------------- #
@app.get("/fetch")
def fetch(url: str) -> dict:
    # VULNERABLE: the server fetches whatever URL you give it. On a real network
    # this reaches internal-only hosts (cloud metadata, admin panels, etc.).
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:  # noqa: S310
            body = resp.read(2048).decode("utf-8", "replace")
    except Exception as exc:
        raise HTTPException(400, detail=f"fetch error: {exc}")
    return {"url": url, "preview": body}


# --------------------------------------------------------------------------- #
# VULN 8 — OS command injection
# --------------------------------------------------------------------------- #
@app.post("/ping")
def ping(data: PingIn) -> dict:
    # VULNERABLE: host is passed to a shell. Try host = "127.0.0.1; id" or
    # "127.0.0.1 && whoami" to run arbitrary commands.
    flag = "-c" if os.name != "nt" else "-n"
    out = subprocess.run(  # noqa: S602  (shell=True is the whole point)
        f"ping {flag} 1 {data.host}",
        shell=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    return {"cmd": f"ping {flag} 1 {data.host}", "stdout": out.stdout, "stderr": out.stderr}
