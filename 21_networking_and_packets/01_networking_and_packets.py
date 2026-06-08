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
# # Module 21 — Networking & Packets
#
# **Purpose:** Every attack and every defence rides on the network stack. Before you
# can scan, intercept, or harden anything, you need to *see* how a packet travels from
# `socket` call to wire and back. This module is the foundation for the whole
# **Offensive & Defensive Security (White-Hat)** track.
#
# ---
#
# ## ⚠️ Read this first — ethics & the law
#
# This track teaches **white-hat** (authorized, defensive) security. Doing it for real
# without permission is a crime, not a prank.
#
# **Rules of engagement — follow them every single module:**
#
# 1. **Only touch systems you own or have *written* permission to test.** "I was just
#    looking" is not a defence. In the US the relevant law is the **Computer Fraud and
#    Abuse Act (CFAA)**; most countries have an equivalent (UK Computer Misuse Act, etc.).
# 2. **Scope is sacred.** A pentest authorization lists exact hosts/IP ranges. Touch
#    nothing outside it.
# 3. **Everything in this track targets `127.0.0.1` (your own machine) or the bundled
#    `vulnlab` app.** No cell here sends traffic to anyone else — keep it that way.
# 4. **Port scanning a third party can itself be illegal/abusive.** We scan *localhost*.
# 5. When in doubt, **stop and get authorization in writing.**
#
# Practice legally and for free on: TryHackMe, Hack The Box, PortSwigger Web Security
# Academy, OverTheWire, and your own VMs.
#
# ---
#
# **What you'll learn:**
# - The TCP/IP model and what each layer adds to a packet
# - How a TCP connection is born: the 3-way handshake
# - Sockets in Python — the API under every network tool
# - Build a **TCP port scanner** from scratch (against localhost)
# - Craft & read packets with **scapy**, and how this maps to **nmap**

# %%
import socket
import threading
import time

print("Python socket toolkit ready. Target for everything below: 127.0.0.1")

# %% [markdown]
# ## Step 1: The TCP/IP model — layers on layers
#
# Data does not leave your machine in one piece. Each layer **wraps** the layer above
# it (encapsulation), adding its own header:
#
# ```
# Application   |  HTTP / DNS / TLS        what you send ("GET /")
# Transport     |  TCP / UDP               ports, reliability  (TCP 3-way handshake)
# Internet      |  IP                      source/dest IP addresses, routing
# Link          |  Ethernet / Wi-Fi        MAC addresses, the physical hop
# ```
#
# A web request becomes: `[Ethernet [ IP [ TCP [ HTTP ] ] ] ]`. Each device on the path
# peels back only the layers it needs. A **firewall** reads IP+TCP; your **browser**
# reads HTTP. As an attacker or defender you operate at whichever layer the flaw lives.

# %% [markdown]
# ## Step 2: The TCP 3-way handshake
#
# Before any data, TCP opens a connection with three packets — memorize this, it is the
# heartbeat of port scanning:
#
# ```
# client  --- SYN --->          "let's talk, my seq = x"
# client  <-- SYN/ACK ---       "ok, my seq = y, ack x+1"
# client  --- ACK --->          "ack y+1"   → connection ESTABLISHED
# ```
#
# A **port scanner** abuses this: send a SYN to a port and watch the reply.
# - **SYN/ACK back** → port is **open** (something is listening)
# - **RST back** → port is **closed** (nothing listening)
# - **no reply** → **filtered** (a firewall dropped it silently)
#
# A full `connect()` finishes the handshake (what we do below — simple, reliable). A
# **SYN scan** (`nmap -sS`) sends just the SYN and never completes it — "stealthier" and
# faster, but needs raw-socket/root privileges (Step 5).

# %% [markdown]
# ## Step 3: Sockets — the API under every network tool
#
# A **socket** is one endpoint of a connection: `(IP, port)`. `nmap`, `curl`, your
# browser, and the FastAPI server from Module 17 all sit on top of this same API.
#
# Below we spin up a tiny listener on a random free port, connect to it, exchange bytes,
# and tear it down — the whole client/server lifecycle in one cell.

# %%
def start_echo_server(host: str = "127.0.0.1", port: int = 0) -> tuple[socket.socket, int]:
    """Bind a TCP server that echoes one line back. port=0 → OS picks a free port."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)
    actual_port = srv.getsockname()[1]

    def _serve():
        conn, _addr = srv.accept()
        with conn:
            data = conn.recv(1024)
            conn.sendall(b"echo:" + data)

    threading.Thread(target=_serve, daemon=True).start()
    return srv, actual_port


srv, port = start_echo_server()
print(f"Listener up on 127.0.0.1:{port}")

# Client side: connect, send, receive.
with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
    client.sendall(b"hello")
    print("Server replied:", client.recv(1024))

srv.close()

# %% [markdown]
# ## Step 4: Build a TCP port scanner (against localhost)
#
# A connect-scan is just "try to `connect()` to each port; if it succeeds, the port is
# open." `connect_ex` returns `0` on success instead of raising — perfect for scanning.
#
# We open a couple of listeners first so the scan finds *something*, then sweep a range.

# %%
def scan_port(host: str, port: int, timeout: float = 0.3) -> bool:
    """Return True if a TCP connect to host:port succeeds (port open)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0


# Open two known ports so the scan has hits to find.
srv_a, port_a = start_echo_server(port=0)
srv_b, port_b = start_echo_server(port=0)
open_ports = {port_a, port_b}
print("Planted open ports:", sorted(open_ports))

# Sweep a small range around them.
lo = min(open_ports) - 3
hi = max(open_ports) + 3
found = [p for p in range(lo, hi + 1) if scan_port("127.0.0.1", p)]
print(f"Scanned {lo}-{hi}; open: {found}")

srv_a.close()
srv_b.close()

# %% [markdown]
# Scanning ports one at a time is slow — real scanners go **concurrent**. The exercise
# is to thread it.

# %% [markdown]
# ### Exercise 4.1 — A threaded port scanner
#
# **Purpose:** A serial scan of 1000 ports at 0.3s timeout each can take minutes;
# concurrency is what makes scanning practical. You will parallelize the sweep.
#
# Write `threaded_scan(host, ports)` that scans every port in `ports` concurrently
# (use a `ThreadPoolExecutor`) and returns the **sorted list of open ports**.

# %%
from concurrent.futures import ThreadPoolExecutor

# Plant a couple of open ports to find:
_s1, _p1 = start_echo_server(port=0)
_s2, _p2 = start_echo_server(port=0)
target_ports = list(range(min(_p1, _p2) - 20, max(_p1, _p2) + 20))


# TODO: Implement threaded_scan(host, ports, max_workers=100) -> list[int]
# Map scan_port over `ports` with a ThreadPoolExecutor, keep the ones that return True,
# and return them sorted.
def threaded_scan(host: str, ports: list[int], max_workers: int = 100) -> list[int]:
    ...  # your code here


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
def threaded_scan(host: str, ports: list[int], max_workers: int = 100) -> list[int]:
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = pool.map(lambda p: (p, scan_port(host, p)), ports)
    return sorted(p for p, is_open in results if is_open)


t0 = time.perf_counter()
hits = threaded_scan("127.0.0.1", target_ports)
print(f"Open ports: {hits}  (expected {sorted({_p1, _p2})})")
print(f"Scanned {len(target_ports)} ports in {time.perf_counter() - t0:.3f}s")
_s1.close()
_s2.close()

# %% [markdown]
# ## Step 5: Crafting & reading packets with scapy
#
# `socket` works at the transport layer — the OS builds the IP/TCP headers for you.
# To do a **SYN scan**, OS fingerprinting, or to **sniff** traffic, you need to build
# raw packets yourself. That is what [`scapy`](https://scapy.readthedocs.io/) is for.
#
# > **Privilege note (macOS/Linux):** crafting raw packets and sniffing needs **root**
# > (run Jupyter with `sudo`, or use the Wireshark approach in Module 25). The cell
# > below is written so it **runs without root** — it builds packets in memory (no
# > privilege needed) and only *attempts* to send if it can, otherwise it explains what
# > would happen. Same guard pattern as the GPU cells in Modules 14–15.

# %%
try:
    from scapy.all import IP, TCP, sr1  # noqa: F401

    HAVE_SCAPY = True
except Exception as exc:  # pragma: no cover
    HAVE_SCAPY = False
    print("scapy not available:", exc)
    print("Install with: pip install scapy")

if HAVE_SCAPY:
    # Building a packet needs NO privileges — it is just structured bytes in memory.
    syn = IP(dst="127.0.0.1") / TCP(dport=80, flags="S")  # S = SYN flag
    print("Crafted packet:")
    syn.show()
    print("\nThis is a SYN scan probe. Sending it needs root; nmap -sS does exactly")
    print("this at scale. Reading the reply flags (SA=open, RA=closed) classifies the port.")

# %% [markdown]
# ### How this maps to nmap
#
# You will rarely hand-roll a scanner on a real engagement — you use
# [`nmap`](https://nmap.org/book/man.html). But now you know what it does under the hood:
#
# | nmap command | What it does | Your equivalent |
# |--------------|--------------|-----------------|
# | `nmap -sT 127.0.0.1` | TCP **connect** scan | `scan_port` (Step 4) |
# | `nmap -sS 127.0.0.1` | **SYN** ("stealth") scan | the scapy SYN (Step 5) |
# | `nmap -sV 127.0.0.1` | service **version** detection | Module 22 (banner grabbing) |
# | `nmap -O 127.0.0.1` | OS fingerprinting | TCP/IP quirks via scapy |
# | `nmap -p- 127.0.0.1` | all 65535 ports | `threaded_scan` over `range(1, 65536)` |
#
# Try it on your own machine: `nmap -sT -p 1-1000 127.0.0.1` (install via
# `brew install nmap`). Notice it finds the same kinds of open ports your scanner does.

# %% [markdown]
# ### Exercise 5.1 — Classify a SYN-scan reply
#
# **Purpose:** A scanner is only useful if it interprets replies correctly. Given the
# TCP flags in a SYN-scan response, decide the port's state.
#
# Write `classify(flags)` where `flags` is a string like `"SA"`, `"RA"`, or `""`:
# - `"SA"` (SYN+ACK) → `"open"`
# - `"RA"` or `"R"` (RST) → `"closed"`
# - `""` (no reply) → `"filtered"`

# %%
# TODO: Implement classify(flags: str) -> str
def classify(flags: str) -> str:
    ...  # your code here


# %% jupyter={"source_hidden": true} tags=["solution"]
# SOLUTION
def classify(flags: str) -> str:
    f = set(flags.upper())
    if {"S", "A"} <= f:
        return "open"
    if "R" in f:
        return "closed"
    return "filtered"


for fl in ["SA", "RA", "R", ""]:
    print(f"flags={fl!r:5} -> {classify(fl)}")

# %% [markdown]
# ## What you learned
#
# | Concept | Why it matters in security |
# |---------|----------------------------|
# | TCP/IP layers | Pick the layer the vulnerability lives at |
# | 3-way handshake | Every port scan reads the SYN/ACK/RST reply |
# | Sockets | The API under nmap, curl, and your scanner |
# | Connect vs SYN scan | Trade-off: simple/noisy vs stealthy/root-only |
# | scapy ↔ nmap | Hand-rolled understanding → real-world tooling |
#
# ## Further reading
#
# - **TCP** — RFC 9293 (modern TCP spec, supersedes 793): https://www.rfc-editor.org/rfc/rfc9293
# - **Nmap reference guide** (port states, scan types): https://nmap.org/book/man.html
# - **Scapy documentation**: https://scapy.readthedocs.io/
# - **Computer Fraud and Abuse Act (CFAA) overview** — why authorization matters:
#   https://www.justice.gov/jm/jm-9-48000-computer-fraud
# - Beej's Guide to Network Programming (sockets, the classic): https://beej.us/guide/bgnet/
#
# **Next:** [Module 22 — Recon & Scanning →](../22_recon_and_scanning/) — turn open
# ports into *named services and versions*, the recon step of a real engagement.
