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
# # Module 25 — Traffic Analysis & Crypto Attacks
#
# **Purpose:** Data in motion and data at rest are only as safe as the crypto protecting
# them. This module shows two things attackers exploit constantly: **unencrypted traffic**
# (anything over plain HTTP is readable on the wire) and **naive cryptography** (ECB
# leaks patterns, fast/unsalted hashes crack, non-constant-time comparisons leak secrets
# through timing). It extends the primitives from Module 18 into their *failure modes*.
#
# **Prerequisites:** Modules 18 and 21 (crypto primitives, packets).
#
# > ♻️ **Ethics reminder (Module 21):** sniff only traffic you own. Everything here is
# > loopback (`127.0.0.1`) and locally-generated ciphertext. Capturing other people's
# > traffic is wiretapping.
#
# **What you'll learn:**
# - **Packet sniffing** with scapy (and the Wireshark/tcpdump equivalent)
# - **HTTP vs HTTPS** — why plaintext protocols leak credentials
# - The **TLS handshake** at a glance
# - **Crypto pitfalls:** ECB pattern leakage, weak/unsalted hashes, **timing attacks**

# %%
import socket
import threading

print("Traffic + crypto lab ready. Wire targets: 127.0.0.1 only.")

# %% [markdown]
# ## Step 1: Sniffing packets
#
# A **sniffer** reads frames off a network interface. On a switched/encrypted network
# you only see your own traffic; on open Wi-Fi or with ARP spoofing an attacker sees
# more. The standard tools are **Wireshark** (GUI) and **tcpdump** (CLI):
#
# ```bash
# sudo tcpdump -i lo0 -A 'tcp port 8000'     # capture loopback HTTP, print ASCII
# ```
#
# scapy can sniff too — but raw capture needs **root**. The cell guards for that and
# falls back to *dissecting a packet we build in memory* (no privileges needed), so the
# notebook always runs.

# %%
try:
    from scapy.all import IP, TCP, Raw, sniff  # noqa: F401
    HAVE_SCAPY = True
except Exception as exc:  # pragma: no cover
    HAVE_SCAPY = False
    print("scapy not available (pip install scapy):", exc)

if HAVE_SCAPY:
    # Build a packet that looks like an HTTP login POST, then dissect it like a sniffer
    # would — no root required to parse bytes we already hold.
    pkt = IP(src="10.0.0.5", dst="10.0.0.9") / TCP(sport=44321, dport=80) / Raw(
        load=b"POST /login HTTP/1.1\r\nHost: site\r\n\r\nuser=alice&password=hunter2"
    )
    print("Dissected captured packet:")
    print("  src:", pkt[IP].src, "-> dst:", pkt[IP].dst, "dport:", pkt[TCP].dport)
    body = pkt[Raw].load.decode()
    print("  payload (plaintext!):", body.splitlines()[-1])
    print("\nTo capture LIVE loopback traffic: sudo python -c \"from scapy.all import "
          "sniff; sniff(iface='lo0', prn=lambda p: p.summary(), count=5)\"")

# %% [markdown]
# ## Step 2: HTTP is plaintext — see the credentials on the wire
#
# Over plain **HTTP**, the request (including a password) crosses the network in the
# clear. We prove it without any external traffic: a local server reads the raw bytes a
# client sends and we print them — exactly what a sniffer between them would see.

# %%
def start_capture_server() -> tuple[socket.socket, int, list]:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    captured: list = []

    def _serve():
        conn, _ = srv.accept()
        with conn:
            captured.append(conn.recv(4096))
            conn.sendall(b"HTTP/1.1 200 OK\r\n\r\nlogged in")
    threading.Thread(target=_serve, daemon=True).start()
    return srv, srv.getsockname()[1], captured


srv, port, captured = start_capture_server()
with socket.create_connection(("127.0.0.1", port)) as c:
    c.sendall(b"POST /login HTTP/1.1\r\nHost: x\r\n\r\nuser=alice&password=hunter2")
    c.recv(1024)

print("Bytes seen on the wire (HTTP — anyone sniffing reads this):")
print(" ", captured[0].decode())
print("\n--> password=hunter2 is right there. HTTPS (TLS) would encrypt this whole body.")
srv.close()

# %% [markdown]
# ## Step 3: The TLS handshake (why HTTPS is safe)
#
# **TLS** turns the readable stream above into ciphertext. Simplified TLS 1.3 handshake:
#
# ```
# client --- ClientHello --->        supported ciphers, key share
# client <-- ServerHello  ---        chosen cipher, key share, certificate
#        (both derive the same session keys via Diffie-Hellman)
# client <-> [encrypted application data]
# ```
#
# Two guarantees: **confidentiality** (eavesdroppers see only ciphertext) and
# **authentication** (the certificate, signed by a CA, proves you're talking to the real
# server — the asymmetric signatures from Module 18). You can inspect a live handshake
# with `openssl s_client -connect example.com:443` or Wireshark's TLS dissector.

# %% [markdown]
# ## Step 4: Crypto pitfall — ECB mode leaks patterns
#
# Encryption is only as good as its **mode**. **ECB** encrypts each 16-byte block
# independently, so *identical plaintext blocks produce identical ciphertext blocks*.
# Structure in the plaintext survives into the ciphertext (the famous "ECB penguin").

# %%
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

key = b"0123456789abcdef"  # 16-byte AES key (demo only)

def aes_ecb_encrypt(data: bytes) -> bytes:
    enc = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    return enc.update(data) + enc.finalize()

# 4 identical 16-byte blocks of plaintext:
plaintext = b"YELLOW SUBMARINE" * 4
ct = aes_ecb_encrypt(plaintext)
blocks = [ct[i:i + 16] for i in range(0, len(ct), 16)]
print("Ciphertext blocks (ECB):")
for b in blocks:
    print(" ", b.hex())
print("Identical plaintext blocks -> identical ciphertext blocks:",
      blocks[0] == blocks[1] == blocks[2] == blocks[3])
print("--> ECB leaks structure. Use an authenticated mode: AES-GCM (or Fernet, M18).")

# %% [markdown]
# ### Exercise 1 — Detect ECB from ciphertext alone
#
# **Purpose:** Mode-detection is a real cryptanalysis skill (Cryptopals challenge 8). You
# can spot ECB *without the key* — it's the only common mode with repeated blocks.
#
# Write `looks_like_ecb(ciphertext, block_size=16)` that returns `True` if any 16-byte
# block repeats. Test it on the ECB ciphertext above (expect `True`) and on random bytes
# (expect `False`).

# %%
import os as _os

# TODO: Implement looks_like_ecb(ciphertext: bytes, block_size: int = 16) -> bool
def looks_like_ecb(ciphertext: bytes, block_size: int = 16) -> bool:
    ...  # your code here


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
def looks_like_ecb(ciphertext: bytes, block_size: int = 16) -> bool:
    blocks = [ciphertext[i:i + block_size] for i in range(0, len(ciphertext), block_size)]
    return len(blocks) != len(set(blocks))


print("ECB ciphertext flagged:", looks_like_ecb(ct))
print("Random bytes flagged:  ", looks_like_ecb(_os.urandom(64)))

# %% [markdown]
# ## Step 5: Crypto pitfall — weak & unsalted hashes
#
# Recap from Modules 18/24, now from the attacker's angle. **MD5/SHA-1 are broken** for
# security (practical collisions). Worse, **unsalted** hashes mean identical passwords
# share a hash — so one cracked hash cracks every user who reused that password, and
# rainbow tables reverse them instantly.

# %%
import hashlib

users = {"alice": "hunter2", "bob": "hunter2", "carol": "letmein"}  # bob reused alice's
hashes = {u: hashlib.md5(p.encode()).hexdigest() for u, p in users.items()}
print("Unsalted MD5 'database':")
for u, h in hashes.items():
    print(f"  {u:6} {h}")
print("alice and bob share a hash:", hashes["alice"] == hashes["bob"],
      "-> crack one, crack both. Salt + bcrypt fixes this (M24).")

# %% [markdown]
# ## Step 6: Crypto pitfall — timing attacks
#
# Comparing secrets (HMAC tags, tokens, passwords) with `==` **returns early** on the
# first mismatching byte. The *time taken* leaks how many leading bytes were correct —
# enough to forge a secret byte-by-byte. We make the leak visible by counting byte
# comparisons (a deterministic proxy for time).

# %%
SECRET = b"s3cr3t-token-value"

def insecure_equal(a: bytes, b: bytes) -> tuple[bool, int]:
    """== semantics: stop at first mismatch. Returns (match, bytes_compared)."""
    compared = 0
    if len(a) != len(b):
        return False, 0
    for x, y in zip(a, b):
        compared += 1
        if x != y:
            return False, compared
    return True, compared

# Wrong on byte 1 vs wrong on byte 5: the comparison count (≈ time) differs and leaks
# how much of our guess was right — an attacker climbs the secret one byte at a time.
g1 = b"X" + SECRET[1:]   # first byte wrong
g2 = SECRET[:5] + b"X" + SECRET[6:]  # wrong only at byte 5
print("guess wrong at byte 0 -> bytes compared:", insecure_equal(g1, SECRET)[1])
print("guess wrong at byte 5 -> bytes compared:", insecure_equal(g2, SECRET)[1])
print("--> the count leaks the prefix length. Fix: constant-time compare.")

# %% [markdown]
# ### Exercise 2 — Close the timing leak
#
# **Purpose:** The fix is to compare in **constant time** regardless of where the
# mismatch is — `hmac.compare_digest` (the `constant_time_equal` from Module 18).
#
# Write `constant_time_equal(a, b)` that always inspects every byte (no early return) and
# returns a bool. Then confirm it still distinguishes correct from incorrect, while not
# short-circuiting. (In production, just call `hmac.compare_digest`.)

# %%
import hmac

# TODO: Implement constant_time_equal(a: bytes, b: bytes) -> bool without early return.
# Hint: XOR each byte pair, OR the results into an accumulator, check it's 0 at the end.
def constant_time_equal(a: bytes, b: bytes) -> bool:
    ...  # your code here


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
def constant_time_equal(a: bytes, b: bytes) -> bool:
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y  # accumulates any difference; never returns early
    return result == 0


print("correct token:", constant_time_equal(SECRET, SECRET))
print("wrong token:  ", constant_time_equal(b"X" + SECRET[1:], SECRET))
print("matches stdlib:", constant_time_equal(SECRET, SECRET) == hmac.compare_digest(SECRET, SECRET))

# %% [markdown]
# ## What you learned
#
# | Pitfall | Consequence | Fix |
# |---------|-------------|-----|
# | Plain HTTP | credentials readable on the wire | TLS/HTTPS everywhere |
# | ECB mode | plaintext patterns leak | authenticated mode (AES-GCM) |
# | MD5/SHA-1, unsalted | collisions, rainbow tables, shared hashes | bcrypt/argon2 + salt |
# | `==` on secrets | timing leaks the prefix | `hmac.compare_digest` |
#
# ## Further reading
#
# - **Cryptopals Crypto Challenges** (hands-on, incl. ECB detection & padding oracle):
#   https://cryptopals.com/
# - **TLS 1.3** — RFC 8446: https://www.rfc-editor.org/rfc/rfc8446
# - **Wireshark User's Guide**: https://www.wireshark.org/docs/wsug_html_chunked/
# - **OWASP Cryptographic Storage Cheat Sheet**:
#   https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
# - **Padding oracle attack** (Vaudenay) — overview:
#   https://en.wikipedia.org/wiki/Padding_oracle_attack
#
# **Next:** [Module 26 — Capstone Pentest →](../26_capstone_pentest/) — run a full
# engagement against vulnlab: recon, exploit chain, findings report, and remediation.
