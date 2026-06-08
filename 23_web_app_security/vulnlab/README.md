# vulnlab — intentionally vulnerable target app

> ⚠️ **WARNING — INTENTIONALLY INSECURE.**
> This app ships real, exploitable vulnerabilities on purpose. **Bind it to
> `127.0.0.1` only. Never deploy it, never expose it to a network, never run it on a
> shared machine.** It exists solely as a practice target for Modules 23–26 — systems
> *you own and are authorized to test*.

A tiny FastAPI app with a database of users, notes, and comments — riddled with the
classic web flaws so you can find, exploit, and then **fix** them.

## Run

```bash
# from the repo root (so `vulnlab` is importable) or from 23_web_app_security/
uvicorn vulnlab.main:app --host 127.0.0.1 --port 8000 --reload
```

- Interactive docs (Swagger): http://127.0.0.1:8000/docs
- The SQLite DB (`vulnlab.db`) is **re-created and re-seeded on every startup**, so you
  can hammer it and just restart to reset.

## Seeded accounts (plaintext passwords — a vuln in itself)

| username | password      | role  | has a private note |
|----------|---------------|-------|--------------------|
| alice    | `hunter2`     | admin | yes (note id 2)    |
| bob      | `password123` | user  | yes (note id 4)    |
| carol    | `letmein`     | user  | no                 |

## Vulnerability inventory (what each module exploits)

| Endpoint | Flaw | OWASP / Module |
|----------|------|----------------|
| `POST /login` | SQL injection (auth bypass), plaintext passwords, no rate limit | A03 Injection / A07 — M23, M24 |
| `GET /search?q=` | SQL injection (UNION exfiltration) | A03 Injection — M23 |
| `GET /notes/{id}` | IDOR — no ownership check, reads private notes | A01 Broken Access Control — M23 |
| `GET /profile/{id}` | IDOR — leaks any user's `api_token` | A01 Broken Access Control — M23 |
| `GET /greet?name=` | Reflected XSS | A03 Injection (XSS) — M23 |
| `POST /comments` + `GET /comments` | Stored XSS | A03 Injection (XSS) — M23 |
| `GET /fetch?url=` | SSRF | A10 SSRF — M23 |
| `POST /ping` | OS command injection | A03 Injection — M23 |
| weak `token` = username | Broken authentication | A07 — M24 |

## Quick smoke test (all localhost)

```bash
# SQLi auth bypass — log in as alice without her password:
curl -s -X POST 127.0.0.1:8000/login \
  -H 'content-type: application/json' \
  -d '{"username":"alice","password":"x'"'"' OR '"'"'1'"'"'='"'"'1"}'

# IDOR — read someone else's private note:
curl -s 127.0.0.1:8000/notes/2

# Reflected XSS — payload echoed unescaped:
curl -s '127.0.0.1:8000/greet?name=<script>alert(1)</script>'
```

The modules walk through each of these in Python with `requests`, explain the root
cause, and show the fix (parameterized queries, output encoding, authz checks,
allow-lists, `subprocess` without a shell).
