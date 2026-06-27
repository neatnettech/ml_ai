# Module 41 — Networking Deep-Dive

**Purpose:** Every networked program — a browser, `curl`, your FastAPI server, a port
scanner — bottoms out in the same handful of system calls: `socket`, `bind`, `listen`,
`accept`, `connect`, `send`, `recv`. [Module 21](../21_networking_and_packets/) showed
the *picture* in Python (the TCP/IP layers, the handshake, a port scanner). This module
goes underneath it: you write the **BSD sockets API in C** by hand, build a TCP echo
client/server, contrast it with UDP, define a small request/response **protocol**, and
write a **concurrent server**. Every demo `fork()`s its own client *and* server over
`127.0.0.1` on an OS-assigned port, so it runs end-to-end with a single `make` — no
second terminal, no external network.

**Prerequisites:** [Module 37](../37_concurrency/) (processes, `fork`, threads — demo 4
spawns workers) and [Module 28](../28_bits_and_bytes/) (byte order — `htons`/`ntohs`
exist precisely because the wire is big-endian and your Mac is little-endian). Ties
directly to [Module 21](../21_networking_and_packets/): this is the C layer beneath that
Python.

**What you'll learn:**
- The **socket lifecycle** for both server and client, call by call
- `struct sockaddr_in` and why **byte order** (`htons`/`htonl`) is mandatory on the wire
- **TCP vs UDP**: connection + reliable stream vs connectionless datagrams (the API forks)
- Designing a **request/response protocol**: message format, framing, parsing, dispatch
- **Concurrency**: serving many clients with thread-per-connection (and fork-per-conn)
- **Blocking vs non-blocking** I/O, and how all this underlies HTTP and the Backend track

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 41 runs **natively on macOS** (Apple Silicon or Intel) — no container needed.
You only need `clang` + `make` (Xcode Command Line Tools). All traffic is loopback
(`127.0.0.1`); nothing leaves your machine and no port is hard-coded (we bind port `0`
and let the OS pick a free ephemeral port).

```bash
make run        # build + run all four demos over loopback
```

---

## 1. The socket lifecycle

A **socket** is one endpoint of a connection — a file descriptor you read and write like
any other, but backed by the network stack. A TCP exchange uses two distinct sequences:

```
  SERVER                         CLIENT
  socket()                       socket()
  bind(addr)                     connect(addr) ─── 3-way handshake ──▶
  listen(backlog)
  accept()  ◀── returns a NEW fd per client
  recv()/send()  ◀───────────▶  send()/recv()
  close()                        close()
```

The listening socket only *accepts*; each `accept()` returns a **fresh** fd for that one
client, so the listener can keep accepting more. [`01_tcp_echo.c`](01_tcp_echo.c)
(`make run1`) `fork()`s a server child and a client parent in one program:

```
── demo 1 ──
[main] listening on ephemeral port 64060
[server] accepted a client
[server] received: hello over TCP
[server] echoed it back
[client] connected to 127.0.0.1:64060
[client] sent:     hello over TCP
[client] got back: hello over TCP
[main] server child exited, done
```

The key trick that makes this self-contained: `bind` to port `0`, then `getsockname()`
to read back the port the OS chose, and hand that to the client. No fixed port to
collide with, no second terminal.

## 2. `struct sockaddr_in`

An address is passed as a `struct sockaddr *`, but for IPv4 you fill in the concrete
`struct sockaddr_in` and cast:

```c
struct sockaddr_in addr;
memset(&addr, 0, sizeof addr);
addr.sin_family      = AF_INET;                 // IPv4
addr.sin_port        = htons(port);             // 16-bit port, NETWORK byte order
addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);  // 127.0.0.1, NETWORK byte order
```

`AF_INET` selects IPv4; `SOCK_STREAM` (in `socket()`) selects TCP, `SOCK_DGRAM` selects
UDP. `INADDR_LOOPBACK` is `127.0.0.1` — traffic that never leaves the host.

## 3. Byte order — the tie to Module 28

The internet is **big-endian** ("network byte order"); your Mac is **little-endian**.
So *every* multi-byte field that goes on the wire must be converted:

| function | converts | use for |
|----------|----------|---------|
| `htons` | host → network, **s**hort (16-bit) | the port |
| `htonl` | host → network, **l**ong (32-bit) | the IPv4 address |
| `ntohs` | network → host, short | a port you read back (`getsockname`, `recvfrom`) |
| `ntohl` | network → host, long | an address you received |

Forget `htons` on the port and you bind/connect to the *byte-swapped* port — a classic
bug. This is Module 28's endianness made load-bearing.

## 4. The TCP 3-way handshake (conceptually)

Before any application bytes flow, `connect()` and the listening kernel exchange three
segments to agree on starting sequence numbers and open the connection:

```
  client ── SYN ──▶            "let's talk, my seq = x"
  client ◀ SYN-ACK ──          "ok, ack x+1, my seq = y"
  client ── ACK ──▶            "ack y+1"  → connection ESTABLISHED
```

You don't write this — the kernel does it inside `connect()`/`accept()`. (A SYN-only
"half-open" probe is exactly what the stealth scan in Module 21 sends.) The payoff: TCP
gives you a **reliable, ordered byte stream**. The cost: per-connection state and that
round-trip of setup.

## 5. TCP vs UDP

UDP skips all of that. There is no `listen`, no `accept`, no handshake — just datagrams
addressed on every call. [`02_udp.c`](02_udp.c) (`make run2`) mirrors demo 1 with
`sendto`/`recvfrom`:

```
── demo 2 ──
[main] UDP server on ephemeral port 50121
[server] got datagram from 127.0.0.1:51492: hello over UDP
[server] echoed datagram back
[client] sent datagram: hello over UDP
[client] got reply:     hello over UDP
[main] done (note: no handshake ever happened — UDP is connectionless)
```

The API difference *is* the conceptual difference:

| | TCP (`SOCK_STREAM`) | UDP (`SOCK_DGRAM`) |
|---|---|---|
| connection | yes — handshake, then a stream | none — independent datagrams |
| reliability | ordered, retransmitted, no dups | best-effort: may drop/reorder/dup |
| API | `connect`/`accept`, then `send`/`recv` | `sendto`/`recvfrom` with peer each call |
| message boundaries | none (a stream — *you* frame it) | preserved (one datagram = one message) |
| used by | HTTP, SSH, databases | DNS, video/voice, QUIC's base |

## 6. A request/response protocol

Raw `send`/`recv` move bytes; an application needs an agreed **message format** on top.
[`03_protocol.c`](03_protocol.c) (`make run3`) defines a tiny text protocol over TCP —
the same shape as HTTP or Redis: one `\n`-terminated request line, one response line.

```
  SET key value  -> OK            GET key  -> VALUE <v> | NOTFOUND
  ADD a b        -> RESULT <a+b>  PING     -> PONG
```

`ADD` is a miniature **RPC** (remote procedure call): the client invokes a "procedure"
on the server and gets the result back. The server buffers bytes and splits on `\n`
(**framing**: knowing where one message ends), then parses and dispatches each line:

```
── demo 3 ──
[main] protocol server on ephemeral port 64062
[server] PING            -> PONG
[server] GET color       -> NOTFOUND
[server] SET color blue  -> OK
[server] GET color       -> VALUE blue
[server] ADD 19 23       -> RESULT 42
[server] BOGUS x         -> ERR unknown command
[client] PING            <- PONG
[client] GET color       <- NOTFOUND
[client] SET color blue  <- OK
[client] GET color       <- VALUE blue
[client] ADD 19 23       <- RESULT 42
[client] BOGUS x         <- ERR unknown command
[main] done
```

The reason framing matters: `recv()` does **not** respect message boundaries on a TCP
stream — one `recv` may return half a line or three lines. The buffer-and-split loop is
how every line/length-prefixed protocol copes.

## 7. Blocking vs non-blocking

By default these calls **block**: `accept` waits until a client connects, `recv` waits
until bytes arrive. That's simplest and is what all four demos use. The alternatives,
which production servers use to handle thousands of connections per thread:

- **Non-blocking** sockets (`O_NONBLOCK`): calls return immediately with `EWOULDBLOCK`
  instead of waiting.
- **I/O multiplexing** (`select`/`poll`/`kqueue` on macOS, `epoll` on Linux): one thread
  waits on many sockets at once and handles whichever is ready — the event loop behind
  nginx, Redis, and Python's `asyncio`/uvicorn.

## 8. A concurrent server

A single accept→recv→send loop serves one client at a time. To serve many, either
**fork** a child per connection or spawn a **thread** per connection.
[`04_concurrent_server.c`](04_concurrent_server.c) (`make run4`, built with `-pthread`)
runs the accept-loop in a background thread, hands each connection to a worker thread,
and forks a few clients that connect at once. Each reply carries the worker's thread id,
so you can see distinct threads serving distinct clients:

```
── demo 4 ──
[main] concurrent server on ephemeral port 64064, expecting 3 clients
[client 0] reply: thread 12288 handled: hi from client 0
[client 1] reply: thread 61440 handled: hi from client 1
[client 2] reply: thread 45056 handled: hi from client 2
[main] all 3 clients served concurrently, done
```

This is exactly the model behind the **Backend track** (Modules 17–20): a FastAPI app
under `uvicorn`/`gunicorn` is workers (processes/threads) each running an accept loop and
parsing HTTP — a more elaborate version of demo 3's protocol over demo 4's concurrency.
And the connect-scan in [Module 21](../21_networking_and_packets/) is just demo 1's
client half, run against a range of ports.

---

## 9. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`. All exercises
are self-contained (fork-based, loopback) and bounded, so they always terminate — an
unfinished stub exits in a few seconds instead of hanging.

### Exercise 41.1 — Implement the protocol client  (`make ex1`)
A working server is provided in [`exercises/ex1_protocol_client.c`](exercises/ex1_protocol_client.c);
implement `send_request` (connect, send a line, read the reply). Expected (`make sol1`):
```
[client] PING           -> PONG
[client] SET color blue -> OK
[client] GET color      -> VALUE blue
[client] ADD 19 23      -> RESULT 42
```

### Exercise 41.2 — Add a new command  (`make ex2`)
Extend the dispatcher in [`exercises/ex2_new_command.c`](exercises/ex2_new_command.c)
with a `SUB a b` command. Until you do, the stub answers `SUB` with `ERR unknown command`;
the solution replies `RESULT 42`. Expected (`make sol2`):
```
[client] PING       -> PONG
[client] ADD 19 23  -> RESULT 42
[client] SUB 50 8   -> RESULT 42
```

### Exercise 41.3 — An accept-loop  (`make ex3`)
Demo 1's server quits after one client. Implement `run_server` in
[`exercises/ex3_accept_loop.c`](exercises/ex3_accept_loop.c) so it accepts and echoes
for several clients in a row. Three forked clients verify each gets served. Expected
(`make sol3`):
```
[main] echo server (accept-loop) on port 64077, 3 clients
[client 0] echo: ping from client 0
[client 1] echo: ping from client 1
[client 2] echo: ping from client 2
[main] all 3 clients served, done
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **Socket lifecycle** | `socket/bind/listen/accept` (server) vs `socket/connect` (client) — the skeleton of every network program |
| **`struct sockaddr_in`** | How an IPv4 endpoint (family + port + address) is handed to the kernel |
| **Byte order (`htons`/`ntohs`)** | The wire is big-endian; converting is mandatory — Module 28's endianness, for real |
| **TCP vs UDP** | Reliable ordered stream + handshake vs connectionless datagrams; the API mirrors the semantics |
| **Protocol & framing** | `recv` ignores message boundaries; you define a format and split the stream yourself |
| **Concurrency** | Thread/fork-per-connection lets one server serve many clients — the model under FastAPI workers |
| **Blocking vs non-blocking** | Why event loops (`kqueue`/`epoll`) exist once you need many connections per thread |

## Further reading

- **Beej's Guide to Network Programming** (the friendliest complete intro to the C
  sockets API; pairs with this module 1:1): https://beej.us/guide/bgnet/
- **MIT 6.1800 — Computer Systems Engineering** (networking, naming, distributed
  systems — the systems view above the syscalls): https://web.mit.edu/6.1800/
- **TCP/IP Illustrated, Vol. 1** (Stevens/Fall) — the definitive on-the-wire reference
  for what TCP and UDP actually do, packet by packet.

**Next:** Module 42 — Distributed Systems — go from one machine to many: clocks, RPC at
scale, consensus, and the failures that only appear across a network.
*(Not yet built — see [the track plan](../cs-foundations-track.md).)* →
[../42_distributed/README.md](../42_distributed/README.md)
