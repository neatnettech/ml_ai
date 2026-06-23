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
# # Module 18 — Cryptography Deep-Dive
#
# **Purpose:** The primitives authentication stands on — hashing, salting, HMAC,
# symmetric and asymmetric encryption — each demonstrated in code you run and break.
# The payoff: you **build and verify an HS256 JWT by hand**, so the login system you
# assemble in Module 19 is never a black box.
#
# **Prerequisites:** Module 17 (the API you're about to lock down).
#
# Before you can build authentication (Module 19), you need to understand the
# primitives it stands on. This module is **mostly notebook-driven** — no server,
# just code you run to *see* how the maths protects data.
#
# You will learn, hands-on:
#
# 1. **Hashing vs encryption** — one-way vs two-way, and when to use each
# 2. **Salting** — why two users with the same password get different hashes
# 3. **HMAC** — proving a message was not tampered with
# 4. **Symmetric encryption** — one shared key (Fernet / AES)
# 5. **Asymmetric encryption** — public/private key pairs (RSA sign & verify)
# 6. **JWT signatures from scratch** — build and verify an `HS256` token by hand
#
# The reusable helpers live in `crypto_demo.py` next to this notebook.

# %%
import hashlib
import hmac
import secrets

# crypto_demo.py sits beside this notebook
from crypto_demo import (
    make_jwt_hs256,
    verify_jwt_hs256,
    constant_time_equal,
    sign_hs256,
)

print("Crypto toolkit loaded.")

# %% [markdown]
# ## Step 1: Hashing — the one-way street
#
# A **hash** maps any input to a fixed-size fingerprint. It is **one-way**: easy
# to compute, infeasible to reverse. Same input → same hash, always. Change one
# bit of input → the whole hash changes (the "avalanche" effect).
#
# This is what you store instead of a password: you can check a login by hashing
# the attempt and comparing, but a database leak never reveals the actual passwords.

# %%
def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


print("hash('password123') =", sha256_hex("password123"))
print("hash('password124') =", sha256_hex("password124"))  # one char → totally different
print("\nSame input is deterministic:")
print(sha256_hex("hello") == sha256_hex("hello"))

# %% [markdown]
# ### Why raw SHA-256 is NOT enough for passwords
#
# Two problems:
# 1. **It is fast.** Attackers can try billions of guesses per second.
# 2. **It is unsalted.** Identical passwords produce identical hashes, so a
#    precomputed "rainbow table" cracks them in bulk.
#
# The fix (Step 2): a **salt** + a **deliberately slow** algorithm (bcrypt/argon2,
# which you use in Module 19). Here we show the salt idea with SHA-256 to keep it
# transparent.

# %% [markdown]
# ## Step 2: Salting
#
# A **salt** is random bytes mixed into the password before hashing. Stored
# alongside the hash, it ensures two users with the same password get **different**
# hashes — defeating rainbow tables.

# %%
def hash_with_salt(password: str, salt: bytes) -> str:
    return hashlib.sha256(salt + password.encode()).hexdigest()


alice_salt = secrets.token_bytes(16)  # cryptographically random, unique per user
bob_salt = secrets.token_bytes(16)

# Alice and Bob both chose "hunter2" — but the stored hashes differ:
print("Alice:", hash_with_salt("hunter2", alice_salt))
print("Bob:  ", hash_with_salt("hunter2", bob_salt))
print("\nDifferent hashes for the same password — rainbow tables defeated.")

# %% [markdown]
# ### Exercise 2.1 — Verify a password
#
# Login works like this: you stored `(salt, hash)`. A user submits a password
# attempt. Re-hash the attempt **with the same salt** and compare to the stored
# hash. Write `verify_password`.

# %%
# TODO: Implement verify_password(attempt, salt, stored_hash) -> bool
# Re-hash `attempt` with `salt` (use hash_with_salt) and compare to stored_hash.
# Use constant_time_equal on the .encode()'d hex strings (avoid timing leaks).
def verify_password(attempt: str, salt: bytes, stored_hash: str) -> bool:
    ...  # your code here


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
def verify_password(attempt: str, salt: bytes, stored_hash: str) -> bool:
    candidate = hash_with_salt(attempt, salt)
    return constant_time_equal(candidate.encode(), stored_hash.encode())


stored = hash_with_salt("hunter2", alice_salt)
print("Correct password:", verify_password("hunter2", alice_salt, stored))   # True
print("Wrong password:  ", verify_password("guess!!", alice_salt, stored))   # False

# %% [markdown]
# ## Step 3: HMAC — tamper-proof messages
#
# A **hash** proves integrity only if nobody can recompute it. An **HMAC**
# (Hash-based Message Authentication Code) mixes a **secret key** into the hash, so
# only someone holding the key can produce or verify it. This is the core of JWT
# signatures (Step 6).
#
# **Constant-time comparison matters.** Comparing the HMAC with `==` can leak,
# through timing, how many leading bytes matched — enough to forge a signature
# byte by byte. Always use `hmac.compare_digest` (wrapped here as
# `constant_time_equal`).

# %%
secret = b"server-side-secret-key"
message = b"transfer $100 to alice"

tag = hmac.new(secret, message, hashlib.sha256).hexdigest()
print("HMAC tag:", tag)

# Attacker flips the message but cannot recompute a valid tag without the secret:
tampered = b"transfer $100 to mallory"
tampered_tag = hmac.new(secret, tampered, hashlib.sha256).hexdigest()
print("\nVerify original :", constant_time_equal(tag.encode(), tag.encode()))         # True
print("Verify tampered :", constant_time_equal(tag.encode(), tampered_tag.encode()))  # False

# %% [markdown]
# ## Step 4: Symmetric encryption — one shared key
#
# **Hashing is one-way; encryption is two-way.** Symmetric encryption uses **one
# key** to both encrypt and decrypt. `cryptography`'s **Fernet** is a safe, batteries-
# included choice (AES-128-CBC + HMAC under the hood, so it is also tamper-evident).
#
# Use this when *you* hold the key on both ends — e.g. encrypting data at rest.

# %%
from cryptography.fernet import Fernet

key = Fernet.generate_key()  # keep this secret! anyone with it can decrypt
f = Fernet(key)

ciphertext = f.encrypt(b"my secret API token")
print("Ciphertext:", ciphertext[:40], b"...")

plaintext = f.decrypt(ciphertext)
print("Decrypted :", plaintext)

# Fernet detects tampering: flip a byte and decryption raises instead of returning garbage.
from cryptography.fernet import InvalidToken

try:
    f.decrypt(ciphertext[:-1] + bytes([ciphertext[-1] ^ 0x01]))
except InvalidToken:
    print("\nTampered ciphertext rejected (InvalidToken) — integrity protected.")

# %% [markdown]
# ## Step 5: Asymmetric encryption — public/private key pairs
#
# Symmetric keys have a chicken-and-egg problem: how do two strangers share a key
# securely? **Asymmetric** crypto solves it with a **key pair**:
#
# - **Private key** — kept secret. Used to **sign** (and to decrypt).
# - **Public key** — shared freely. Used to **verify** (and to encrypt *to* you).
#
# **Signing** proves authenticity: only the private-key holder could have produced
# a signature, and anyone with the public key can check it. This is how `RS256`
# JWTs and TLS certificates work.

# %%
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

# Generate a key pair (slow — that is normal for RSA).
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

message = b"signed by the server"

# Sign with the PRIVATE key:
signature = private_key.sign(
    message,
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    hashes.SHA256(),
)
print("Signature length:", len(signature), "bytes")

# Anyone can verify with the PUBLIC key — verify() raises on failure, returns None on success:
public_key.verify(
    signature,
    message,
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    hashes.SHA256(),
)
print("Signature verified with the public key.")

# %% [markdown]
# ### Exercise 5.1 — Catch a forged signature
#
# Verification must **fail** if the message was altered after signing. Try to
# verify `signature` against a *different* message and confirm it raises
# `InvalidSignature`.

# %%
# TODO: Verify `signature` against b"a different message".
# Wrap public_key.verify(...) in try/except cryptography.exceptions.InvalidSignature
# and print whether it was (correctly) rejected.


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
from cryptography.exceptions import InvalidSignature

try:
    public_key.verify(
        signature,
        b"a different message",  # not what was signed
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    print("Verified — this should NOT happen!")
except InvalidSignature:
    print("Forged message rejected (InvalidSignature) — exactly right.")

# %% [markdown]
# ## Step 6: A JWT signature, from scratch
#
# A **JWT** (JSON Web Token) is just three base64url parts joined by dots:
#
# ```
# base64url(header) . base64url(payload) . base64url(signature)
# ```
#
# For `HS256`, the signature is `HMAC-SHA256(header.payload, secret)` — exactly the
# HMAC from Step 3. The header and payload are **only encoded, not encrypted** —
# anyone can read them. The signature is what makes the token **unforgeable**: you
# cannot change the payload without invalidating it (you do not know the secret).
#
# `make_jwt_hs256` / `verify_jwt_hs256` in `crypto_demo.py` implement this by hand.

# %%
import json
from crypto_demo import b64url_decode

SECRET = "super-secret-signing-key"

token = make_jwt_hs256({"sub": "alice", "role": "admin"}, SECRET)
print("Token:\n", token)

# The payload is readable by anyone (base64, not encryption):
header_b64, payload_b64, sig_b64 = token.split(".")
print("\nDecoded payload (NOT secret!):", json.loads(b64url_decode(payload_b64)))

# Valid token verifies and returns the payload:
print("\nVerify valid token:", verify_jwt_hs256(token, SECRET))

# %% [markdown]
# ### Exercise 6.1 — Prove tampering is detected
#
# An attacker grabs the token and rewrites the payload to make themselves admin,
# **without** knowing the secret. Show that `verify_jwt_hs256` rejects it.
#
# Steps: decode the payload, change `"role"` to `"superadmin"`, re-encode it, splice
# it back into the token (keeping the original signature), and verify — it must raise.

# %%
# TODO: Forge a token by swapping in a modified payload, then verify it fails.
# 1. payload = json.loads(b64url_decode(payload_b64)); payload["role"] = "superadmin"
# 2. from crypto_demo import b64url_encode; new_payload_b64 = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
# 3. forged = f"{header_b64}.{new_payload_b64}.{sig_b64}"   # old signature, new payload
# 4. verify_jwt_hs256(forged, SECRET) inside try/except ValueError


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
from crypto_demo import b64url_encode

payload = json.loads(b64url_decode(payload_b64))
payload["role"] = "superadmin"  # privilege escalation attempt
new_payload_b64 = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
forged = f"{header_b64}.{new_payload_b64}.{sig_b64}"  # reuse the OLD signature

try:
    verify_jwt_hs256(forged, SECRET)
    print("Accepted forged token — this should NOT happen!")
except ValueError as e:
    print("Forged token rejected:", e)
    print("\nWhy: changing the payload changes the HMAC signing input, so the")
    print("stored signature no longer matches — and the attacker cannot compute")
    print("a new valid one without the secret.")

# %% [markdown]
# ## What you learned
#
# | Primitive | Direction | Key model | Used for |
# |-----------|-----------|-----------|----------|
# | Hash (SHA-256) | one-way | none | fingerprints, integrity |
# | Salted hash (bcrypt/argon2) | one-way | none | **storing passwords** |
# | HMAC | one-way + key | shared secret | **message authentication, JWT HS256** |
# | Symmetric (Fernet/AES) | two-way | shared secret | encrypting data at rest |
# | Asymmetric (RSA) | two-way | public/private | signatures, key exchange, TLS, JWT RS256 |
#
# Crucially: **hashing protects passwords**, **HMAC signs JWTs**, and a JWT's
# payload is *readable* — only its signature is protected.
#
# ## Further reading
#
# - **Crypto 101** (free book — the whole field from first principles):
#   https://www.crypto101.io/
# - **HMAC — RFC 2104** (the original spec, surprisingly readable):
#   https://www.rfc-editor.org/rfc/rfc2104
# - **JWT — RFC 7519** (exactly what you built in Step 6):
#   https://www.rfc-editor.org/rfc/rfc7519
# - **cryptography.io** (the library behind Fernet and the RSA demo):
#   https://cryptography.io/
# - **Latacora — Cryptographic Right Answers** (which primitive to actually pick):
#   https://www.latacora.com/blog/2018/04/03/cryptographic-right-answers/
#
# **Next:** [Module 19 — Authentication: JWT + Password Security →](../19_auth_jwt/01_auth_jwt.ipynb)
# — use `passlib` (bcrypt) and `pyjwt` to turn these primitives into a real login
# system, and lock down the Module 17 API.
