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
# # Module 22 — Reconnaissance & Scanning
#
# **Purpose:** Recon is the first phase of every real engagement — "know the target
# before you touch it." An open port (Module 21) is just a number; recon turns it into
# *"nginx 1.25 running a login form"*. The more you map, the bigger the attack surface
# you understand. This module is the bridge from raw ports to the web attacks in
# Module 23.
#
# **Prerequisites:** Module 21 (sockets, ports, TCP handshakes).
#
# > ♻️ **Ethics reminder (see Module 21):** authorized targets only. Everything here
# > hits `127.0.0.1` / the bundled `vulnlab`. Recon against systems you don't own —
# > even "just looking" — can be illegal.
#
# **What you'll learn:**
# - **Passive vs active** recon — and why passive comes first
# - **Banner grabbing** — read what a service announces about itself
# - **Service/version fingerprinting** over HTTP (headers, error pages, behaviour)
# - **DNS enumeration** basics
# - How all of this maps to `nmap -sV` and friends

# %%
import socket
import threading

print("Recon toolkit ready. Targets: 127.0.0.1 and the in-process vulnlab.")

# %% [markdown]
# ## Step 1: Passive vs active recon
#
# - **Passive recon** touches *third-party* sources, never the target itself: WHOIS,
#   DNS records, Google dorking, certificate transparency logs, GitHub leaks, job posts
#   ("we use Django + Postgres"). It is invisible to the target.
# - **Active recon** sends packets *to the target*: port scans, banner grabs, directory
#   brute-forcing. It is effective but **noisy** — it shows up in the target's logs/IDS.
#
# Methodology: exhaust passive sources first (free intel, zero risk), then go active
# only within your authorized scope. The goal is an **attack surface map**: hosts →
# open ports → services → versions → known-vulnerable components.

# %% [markdown]
# ## Step 2: Banner grabbing
#
# Many services *introduce themselves* the moment you connect (SMTP, FTP, SSH, Redis)
# or in response to a probe (HTTP). That greeting — the **banner** — often leaks the
# exact software and version, which you then cross-reference against CVE databases.
#
# We plant a fake service that announces a version banner, then grab it over a raw
# socket — exactly what `nmap -sV` automates.

# %%
def start_banner_service(banner: bytes, port: int = 0) -> tuple[socket.socket, int]:
    """A toy service that sends a banner on connect (like SSH/SMTP do)."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(1)
    actual = srv.getsockname()[1]

    def _serve():
        conn, _ = srv.accept()
        with conn:
            conn.sendall(banner)
    threading.Thread(target=_serve, daemon=True).start()
    return srv, actual


def grab_banner(host: str, port: int, timeout: float = 1.0) -> str:
    """Connect and read whatever the service volunteers."""
    with socket.create_connection((host, port), timeout=timeout) as s:
        s.settimeout(timeout)
        try:
            return s.recv(1024).decode("utf-8", "replace").strip()
        except socket.timeout:
            return "(no banner — service stayed silent)"


srv, port = start_banner_service(b"220 vsFTPd 3.0.3 ready\r\n")
print("Grabbed banner:", grab_banner("127.0.0.1", port))
print("--> 'vsFTPd 3.0.3' is a precise version to search for known CVEs.")
srv.close()

# %% [markdown]
# ## Step 3: Fingerprinting an HTTP service
#
# HTTP servers don't greet you on connect — you must *probe*. The response **headers**,
# status codes, and error pages reveal the stack. We use the `vulnlab` app from
# Module 23 in-process (via `TestClient`) so nothing leaves the machine.

# %%
import sys
import os

# Make the vulnlab package importable (it lives under 23_web_app_security/), no matter
# whether this notebook runs from the repo root or from its own module folder.
def _add_vulnlab_to_path() -> None:
    p = os.getcwd()
    for _ in range(6):
        cand = os.path.join(p, "23_web_app_security")
        if os.path.isdir(os.path.join(cand, "vulnlab")):
            sys.path.insert(0, cand)
            return
        p = os.path.dirname(p)
    raise RuntimeError("Could not locate 23_web_app_security/vulnlab")

_add_vulnlab_to_path()
from fastapi.testclient import TestClient
from vulnlab.main import app

client = TestClient(app)
client.__enter__()  # triggers startup (DB seed)

resp = client.get("/health")
print("Status:", resp.status_code)
print("Server header:", resp.headers.get("server"))
print("Body:", resp.json())
print("\nThe 'server' header + framework-shaped JSON errors fingerprint this as")
print("a uvicorn/FastAPI app — now you know to look for the OWASP web flaws in M23.")

# %% [markdown]
# ## Step 4: Content discovery — find hidden endpoints
#
# Servers rarely advertise every route. **Content discovery** brute-forces a wordlist of
# common paths and keeps the ones that don't 404 — the same idea as `gobuster`/`ffuf` or
# `nmap`'s http-enum script. Here we probe a small wordlist against vulnlab.

# %%
WORDLIST = ["/", "/health", "/login", "/search", "/admin", "/profile/1",
            "/comments", "/fetch", "/ping", "/secret", "/api", "/notes/1"]

print("Discovered endpoints (status != 404):")
for path in WORDLIST:
    code = client.get(path).status_code
    if code != 404:
        print(f"  {code}  {path}")

# %% [markdown]
# ### Exercise 4.1 — A version-from-banner fingerprinter
#
# **Purpose:** Recon output must be machine-usable. You'll parse a raw banner into a
# structured `(product, version)` so it can be fed to a CVE lookup automatically.
#
# Write `parse_banner(banner)` that pulls the product name and dotted version out of a
# banner string. Examples:
# - `"220 vsFTPd 3.0.3 ready"` → `("vsFTPd", "3.0.3")`
# - no version found → `(None, None)`
#
# Banners are messy (`"SSH-2.0-OpenSSH_8.9p1"` has two version-ish tokens) — a simple
# regex won't be perfect, and that's a realistic lesson in itself.

# %%
import re

# TODO: Implement parse_banner(banner: str) -> tuple[str | None, str | None]
# Hint: a regex like r"([A-Za-z_]+)[ _/]v?(\d+\.\d+[\w.]*)" finds "name version" pairs.
def parse_banner(banner: str) -> tuple[str | None, str | None]:
    ...  # your code here


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
def parse_banner(banner: str) -> tuple[str | None, str | None]:
    m = re.search(r"([A-Za-z][A-Za-z_]+)[ _/-]v?(\d+\.\d+[\w.]*)", banner)
    if not m:
        return None, None
    return m.group(1), m.group(2)


for b in ["220 vsFTPd 3.0.3 ready", "SSH-2.0-OpenSSH_8.9p1", "200 OK no version here"]:
    print(f"{b!r:35} -> {parse_banner(b)}")

# %% [markdown]
# ## Step 5: DNS enumeration
#
# DNS maps names to addresses and leaks structure: subdomains (`mail.`, `vpn.`,
# `staging.`) each expand the attack surface. Basic forward/reverse lookups come free
# with `socket`; subdomain brute-forcing and zone transfers (`dig AXFR`) go deeper.
#
# We resolve `localhost` only (no external queries from this notebook).

# %%
name = "localhost"
print(f"Forward lookup {name!r}:", socket.gethostbyname(name))
try:
    host, aliases, addrs = socket.gethostbyaddr("127.0.0.1")
    print("Reverse lookup 127.0.0.1:", host)
except socket.herror as e:
    print("Reverse lookup failed:", e)

print("\nReal recon: enumerate subdomains with a wordlist + crt.sh certificate logs,")
print("and try `dig AXFR @ns.target.com target.com` for a (mis)configured zone transfer.")

# %% [markdown]
# ### How this maps to nmap & friends
#
# | Tool / command | What it does | This module's version |
# |----------------|--------------|------------------------|
# | `nmap -sV target` | service **version** detection | banner grab + HTTP fingerprint |
# | `nmap --script http-enum` | find common web paths | content discovery (Step 4) |
# | `whatweb http://target` | identify web tech | the `server` header read |
# | `gobuster dir -w list` | directory brute-force | the `WORDLIST` loop |
# | `dnsenum` / `dig` | DNS enumeration | `gethostbyname` (Step 5) |
# | `nmap -O target` | OS fingerprint | TCP/IP quirks (Module 21 scapy) |

# %% [markdown]
# ### Exercise 5.2 — Score the attack surface
#
# **Purpose:** Recon ends with prioritization — which findings deserve attention first.
# Given discovered endpoints, flag the *interesting* ones (auth, server-side fetch,
# anything that takes user input into a sensitive sink).
#
# Write `interesting(paths)` returning the subset whose name suggests risk: contains any
# of `login`, `admin`, `search`, `fetch`, `ping`, `profile`.

# %%
discovered = ["/health", "/login", "/search", "/profile/1", "/comments", "/fetch", "/ping"]

# TODO: Implement interesting(paths: list[str]) -> list[str]
def interesting(paths: list[str]) -> list[str]:
    ...  # your code here


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
def interesting(paths: list[str]) -> list[str]:
    keywords = ("login", "admin", "search", "fetch", "ping", "profile")
    return [p for p in paths if any(k in p.lower() for k in keywords)]


print("High-interest endpoints to attack in Module 23:")
for p in interesting(discovered):
    print("  ", p)

# %%
client.__exit__(None, None, None)  # close the in-process app cleanly

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters |
# |---------|----------------|
# | Passive then active | Free intel first, noisy probing second |
# | Banner grabbing | A version string → a CVE search |
# | HTTP fingerprinting | Headers/errors reveal the stack to attack |
# | Content discovery | Hidden routes = hidden attack surface |
# | DNS enumeration | Subdomains multiply the target list |
#
# ## Further reading
#
# - **OWASP Web Security Testing Guide — Information Gathering**:
#   https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/
# - **Nmap service/version detection**: https://nmap.org/book/vscan.html
# - **crt.sh** (certificate-transparency subdomain recon): https://crt.sh/
# - **ffuf** (fast web fuzzer for content discovery): https://github.com/ffuf/ffuf
# - **MITRE ATT&CK — Reconnaissance (TA0043)**: https://attack.mitre.org/tactics/TA0043/
#
# **Next:** [Module 23 — Web Application Security →](../23_web_app_security/) — take the
# high-interest endpoints you just found and actually exploit them on `vulnlab`.
