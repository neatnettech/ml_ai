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
# # Module 24 — Authentication Attacks & Defense
#
# **Purpose:** Authentication is the front door. **A07: Identification & Authentication
# Failures** is in the OWASP Top 10 because weak login flows are everywhere and the
# payoff for breaking them is total. This module attacks `vulnlab`'s login (online brute
# force), cracks password hashes (offline), then **builds the defences** that stop both —
# bcrypt, rate limiting, lockout, and TOTP MFA. It builds directly on the crypto
# primitives from Module 18 and the auth flow from Module 19.
#
# > ♻️ **Ethics reminder (Module 21):** brute-forcing a login you don't own is a crime
# > (CFAA). Targets here: `vulnlab` on localhost and hashes you generate yourself.
#
# **What you'll learn:**
# - **Online brute force / dictionary attacks** against a live login
# - **Credential stuffing** — why password reuse is catastrophic
# - **Offline cracking** — what `hashcat`/`john` actually do to a leaked hash
# - **Defenses:** bcrypt (slow hashing), rate limiting, account lockout, **TOTP MFA**

# %%
import sys, os

# Locate the vulnlab package (under 23_web_app_security/) regardless of the working dir.
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
client.__enter__()
print("vulnlab login ready. It has NO rate limit and plaintext passwords — for now.")

# %% [markdown]
# ## Step 1: Online dictionary attack
#
# An **online** attack sends guesses to the live login endpoint. Most real passwords are
# weak and appear in public wordlists (`rockyou.txt` has 14M). vulnlab returns **401**
# for a wrong password and **200** for a hit — a perfect oracle, and it never rate-limits
# us. We try a small wordlist against `bob`.

# %%
WORDLIST = ["123456", "qwerty", "letmein", "admin", "password123", "hunter2", "dragon"]
TARGET_USER = "bob"

def try_login(username: str, password: str) -> bool:
    return client.post("/login", json={"username": username, "password": password}).status_code == 200

for i, guess in enumerate(WORDLIST, 1):
    if try_login(TARGET_USER, guess):
        print(f"[{i}] CRACKED {TARGET_USER}:{guess}")
        break
    print(f"[{i}] nope: {guess}")

# %% [markdown]
# **Why it worked:** no rate limit, no lockout, no MFA, and a weak password. Each of
# those is a separate defence you'll add below.

# %% [markdown]
# ### Exercise 1 — Spray, don't pound (password spraying)
#
# **Purpose:** Lockout defences trigger on *many guesses against one account*. Attackers
# evade them by **password spraying** — trying *one* common password against *many*
# usernames. You'll flip the loop.
#
# Write `spray(usernames, password)` that tries the single `password` against every
# username and returns the list of `(username, password)` pairs that logged in. Test it
# with password `"letmein"` against `["alice", "bob", "carol"]`.

# %%
# TODO: Implement spray(usernames, password) -> list[tuple[str, str]]
def spray(usernames: list[str], password: str) -> list[tuple[str, str]]:
    ...  # your code here


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
def spray(usernames: list[str], password: str) -> list[tuple[str, str]]:
    return [(u, password) for u in usernames if try_login(u, password)]


print("Spray hits for 'letmein':", spray(["alice", "bob", "carol"], "letmein"))

# %% [markdown]
# ## Step 2: Credential stuffing
#
# **Credential stuffing** reuses *username:password pairs leaked from other breaches*. It
# works because people reuse passwords. It's not a guess — it's a replay. Defences:
# **MFA** (the stolen password isn't enough) and breach-password screening
# (Have I Been Pwned's k-anonymity API). The attack code is identical to Step 1 but the
# wordlist is real leaked pairs.

# %% [markdown]
# ## Step 3: Offline cracking — what hashcat/john do
#
# Once an attacker has the **password database** (via the SQLi from Module 23), they
# crack it *offline* — no rate limit, billions of guesses/second on a GPU. This is why
# **how you hash** matters enormously.
#
# - **Unsalted fast hash (MD5/SHA-256):** identical passwords → identical hashes;
#   precomputed *rainbow tables* reverse them instantly.
# - **Salted slow hash (bcrypt/argon2):** each hash is unique and *deliberately slow*,
#   so brute force is millions of times more expensive.
#
# We crack a fast unsalted hash with a dictionary (the core loop of `hashcat`/`john`),
# then show why bcrypt defeats the same attack.

# %%
import hashlib

# Attacker stole this unsalted SHA-256 hash. Crack it with a wordlist:
stolen_hash = hashlib.sha256(b"hunter2").hexdigest()

def crack_sha256(target_hash: str, wordlist: list[str]) -> str | None:
    for word in wordlist:
        if hashlib.sha256(word.encode()).hexdigest() == target_hash:
            return word
    return None

print("Cracked fast hash ->", crack_sha256(stolen_hash, WORDLIST))

# %% [markdown]
# ## Step 4: Defense (1) — bcrypt, the slow salted hash
#
# bcrypt (from Module 18/19) salts automatically and has a tunable **cost factor**: each
# extra cost doubles the work. A correct guess still verifies, but trying a whole
# wordlist becomes painfully slow — the attacker's economics collapse.

# %%
import bcrypt

# Store passwords the right way:
stored = bcrypt.hashpw(b"hunter2", bcrypt.gensalt(rounds=10))
print("bcrypt hash:", stored.decode()[:40], "...")

# Verify (login):
print("Correct password verifies:", bcrypt.checkpw(b"hunter2", stored))
print("Wrong password rejected:  ", bcrypt.checkpw(b"wrong", stored))

# Note: every run produces a DIFFERENT hash for the same password (random salt):
print("Salted (two hashes of same pw differ):",
      bcrypt.hashpw(b"hunter2", bcrypt.gensalt(rounds=10))
      != bcrypt.hashpw(b"hunter2", bcrypt.gensalt(rounds=10)))

# %% [markdown]
# ## Step 5: Defense (2) — rate limiting & account lockout
#
# Even with bcrypt, an *online* attack should be throttled. Two layers:
# - **Rate limiting:** cap attempts per IP/time window (e.g. 5 / minute).
# - **Account lockout:** after N consecutive failures, lock the account briefly.
#
# Here's a minimal lockout tracker — the logic a real login handler wraps around the
# password check.

# %%
import time

class LoginGuard:
    """Locks an account after `max_fails` failures within `window` seconds."""
    def __init__(self, max_fails: int = 5, window: float = 60.0, lock_for: float = 300.0):
        self.max_fails, self.window, self.lock_for = max_fails, window, lock_for
        self._fails: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}

    def is_locked(self, user: str, now: float) -> bool:
        return now < self._locked_until.get(user, 0)

    def record_failure(self, user: str, now: float) -> None:
        recent = [t for t in self._fails.get(user, []) if now - t < self.window]
        recent.append(now)
        self._fails[user] = recent
        if len(recent) >= self.max_fails:
            self._locked_until[user] = now + self.lock_for
            self._fails[user] = []

    def record_success(self, user: str) -> None:
        self._fails.pop(user, None)


guard = LoginGuard(max_fails=3, window=60, lock_for=300)
t = 1000.0  # simulated clock (Date.now() is fine in real code; fixed here for determinism)
for attempt in range(5):
    if guard.is_locked("bob", t):
        print(f"attempt {attempt}: BLOCKED — account locked")
    else:
        guard.record_failure("bob", t)
        print(f"attempt {attempt}: failed login recorded "
              f"({'now locked' if guard.is_locked('bob', t + 0.1) else 'still open'})")
    t += 1

# %% [markdown]
# ### Exercise 2 — Wrap the login behind the guard
#
# **Purpose:** Tie the defence to the attack — a guarded login should defeat the Step-1
# brute force. Write `guarded_login(guard, user, password, now)` that:
# 1. returns `"locked"` if the account is locked,
# 2. else checks the password (use the `PASSWORDS` dict of bcrypt hashes below),
# 3. on success calls `record_success` and returns `"ok"`,
# 4. on failure calls `record_failure` and returns `"bad"`.
#
# Then run the Step-1 wordlist through it and confirm the account **locks** before the
# real password (`password123`) is ever reached.

# %%
PASSWORDS = {"bob": bcrypt.hashpw(b"password123", bcrypt.gensalt(rounds=8))}

# TODO: Implement guarded_login(guard, user, password, now) -> str
def guarded_login(guard: "LoginGuard", user: str, password: str, now: float) -> str:
    ...  # your code here


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
def guarded_login(guard: "LoginGuard", user: str, password: str, now: float) -> str:
    if guard.is_locked(user, now):
        return "locked"
    if user in PASSWORDS and bcrypt.checkpw(password.encode(), PASSWORDS[user]):
        guard.record_success(user)
        return "ok"
    guard.record_failure(user, now)
    return "bad"


g = LoginGuard(max_fails=3, window=60, lock_for=300)
clock = 2000.0
attack_list = ["123456", "qwerty", "letmein", "password123"]  # real pw is last
for guess in attack_list:
    result = guarded_login(g, "bob", guess, clock)
    print(f"guess={guess:12} -> {result}")
    clock += 1
print("--> locked out before reaching the real password. Brute force defeated.")

# %% [markdown]
# ## Step 6: Defense (3) — TOTP multi-factor authentication
#
# MFA defeats stolen/guessed passwords: the attacker also needs a **time-based one-time
# code** (TOTP, RFC 6238) from the user's authenticator app. The server and app share a
# secret and both compute the same 6-digit code from the current time.

# %%
try:
    import pyotp
    HAVE_PYOTP = True
except Exception as exc:  # pragma: no cover
    HAVE_PYOTP = False
    print("pyotp not installed (pip install pyotp):", exc)

if HAVE_PYOTP:
    secret = pyotp.random_base32()          # provisioned once, stored per user
    totp = pyotp.TOTP(secret)
    code = totp.now()                        # what the user's app shows right now
    print("Provisioning secret:", secret)
    print("Current 6-digit code:", code)
    print("Server verifies code:", totp.verify(code))
    print("A stale/guessed code fails:", totp.verify("000000"))
    print("\nEven with bob's password, an attacker without this code cannot log in.")

# %%
client.__exit__(None, None, None)

# %% [markdown]
# ## What you learned
#
# | Attack | Defense |
# |--------|---------|
# | Online dictionary / brute force | rate limiting + account lockout |
# | Password spraying | lockout-by-IP, breach-password screening |
# | Credential stuffing | **MFA**, HIBP screening |
# | Offline hash cracking | bcrypt/argon2 (slow, salted) — never fast/unsalted |
# | Stolen password | **TOTP MFA** |
#
# Defence in depth: no single control is enough. Slow hashing buys time *offline*,
# throttling buys time *online*, and MFA makes a leaked password useless.
#
# ## Further reading
#
# - **OWASP A07: Identification & Authentication Failures**:
#   https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/
# - **OWASP Password Storage Cheat Sheet** (bcrypt/argon2 guidance):
#   https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
# - **NIST SP 800-63B** — modern auth/password rules (no forced rotation, screen breaches):
#   https://pages.nist.gov/800-63-3/sp800-63b.html
# - **TOTP** — RFC 6238: https://www.rfc-editor.org/rfc/rfc6238
# - **Have I Been Pwned — Pwned Passwords (k-anonymity API)**:
#   https://haveibeenpwned.com/API/v3#PwnedPasswords
# - **hashcat** (the standard offline cracker, for context): https://hashcat.net/hashcat/
#
# **Next:** [Module 25 — Traffic & Crypto Attacks →](../25_traffic_and_crypto_attacks/) —
# sniff the wire, inspect TLS, and break naive cryptography.
