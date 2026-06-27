# Module 42 — Distributed Systems

**Purpose:** A distributed system is many computers cooperating over an unreliable
network to look like one — and almost every hard part comes from two facts: the network
can drop, delay, duplicate, or reorder messages, and there is no shared clock. This
module builds intuition for the four pillars that tame that chaos: **RPC** (calling
another machine), **logical clocks** (ordering events without a shared clock),
**replication** (surviving crashes by keeping copies), and **consensus / Raft** (a
cluster agreeing on one log even as nodes fail). The canonical course here, MIT 6.5840
(formerly 6.824), builds these in **Go** with real RPCs and a real Raft. To keep this
track **self-contained and verifiable**, we instead re-cast the *concepts* as
**deterministic in-process simulations in C**: nodes are structs, the "network" is a
function call or a small queue, and every failure is *scripted* rather than random — so
`make run` reproduces the exact traces below every time, with no cluster to stand up.

**Prerequisites:** Module 37 (Concurrency — threads, races, why coordination is hard)
and Module 41 (Networking Deep-Dive — TCP/IP and RPC over real sockets). This module is
the "what could go wrong, and how do we agree anyway" layer above those.

**What you'll learn:**
- **RPC semantics:** why a lost reply forces timeouts + retries, and how *idempotency*
  or request-id dedup turns at-least-once into safe at-most-once ("exactly-once")
- **Logical clocks:** Lamport's rule for a causal total order, and vector clocks for
  *detecting concurrency* — and why physical wall clocks can't do either
- **Replication & quorums:** how a lagging backup serves a stale read, and why
  **R + W > N** (read + write quorums overlap) eliminates it
- **Consensus (Raft):** terms, one-vote-per-term, majority elections, commit-on-majority
  log replication, and self-healing re-election after a leader crash

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

> **Honesty note:** Demo 4 is a *teaching simulation* of Raft, not a production-correct
> implementation. It models terms, vote-majorities, commit-on-majority, and re-election
> on a single-threaded deterministic event loop — it does **not** model randomized
> election timers, real RPC failures, the full log-matching/safety rules, persistence,
> or snapshots. For the real algorithm and its proofs, read the Raft paper (below).

## Setup

Module 42 runs **natively on Apple Silicon** — no container, no cluster, no Go. You only
need `clang` + `make` (Xcode Command Line Tools):

```bash
make run            # build + run all four simulations
make sol1           # see a reference solution
```

Everything is portable C11; it also builds on Linux or in the x86-64 `setup/` container.

---

## 1. RPC: timeouts, retries, and delivery semantics

A **Remote Procedure Call** makes calling code on another machine look like a local
function call. [`01_rpc.c`](01_rpc.c) (`make run1`) models the client, the "network",
and a server handler in one process, then injects the two failures every RPC system
must survive: a **dropped reply** and a **duplicated request**.

```
make run1
```
```
=== 2. The network DROPS the reply ===
  client: deposit(+50)
  server applied it: balance = 200
  ...but the reply packet is LOST. The client waits, hears nothing.
  The client cannot tell "request lost" from "reply lost" — so it must
  use a TIMEOUT and then RETRY. Watch what a blind retry does next.

=== 3. Blind retry with at-LEAST-once (no dedup) — double-counts! ===
  client times out, retries: deposit(+50)
  server applied it AGAIN: balance = 250  <- BUG: +50 counted twice

=== 4. Same scenario with at-MOST-once (request_id dedup) ===
  client: deposit(+50), request #7
  server applied it: balance = 150
  ...reply is LOST. Client times out and RETRIES the SAME request #7:
    [server] request #7 already applied, ignoring duplicate
  server reply: balance = 150  <- correct: retry was safe (idempotent)
```

A lost reply is **indistinguishable** from a lost request, so the client must time out
and retry — which makes the request arrive *at least once*. That is only correct if the
operation is idempotent, **or** the server dedups by request id (*at-most-once*).
"Exactly-once" is just at-least-once delivery plus server-side dedup.

## 2. Logical clocks: ordering events without a shared clock

Clocks on different machines drift and can't be perfectly synced, so wall-clock
timestamps can't order events across nodes. **Lamport clocks** (a single counter:
`tick` on local/send, `max(local, incoming)+1` on receive) give a total order that
*respects causality*. **Vector clocks** go further and *detect concurrency*.
[`02_logical_clocks.c`](02_logical_clocks.c) (`make run2`) runs a fixed 3-node script:

```
make run2
```
```
=== Lamport logical clocks across 3 nodes ===
  e1  P0 local            L0=1
  e2  P0 send m1 ->P1     L0=2 (m1 carries 2)
  e3  P1 recv m1          L1=max(0,2)+1=3
  e4  P1 send m2 ->P2     L1=4 (m2 carries 4)
  e5  P2 recv m2          L2=max(0,4)+1=5
  e6  P2 local            L2=6

  Lamport timestamps respect causality: e1<e2<e3<e4<e5<e6 (1<2<3<4<5<6).

=== Vector clocks: detecting concurrency ===
  compare A=[1,1,0] (P1 recv m1)  vs  B=[0,0,1] (P2 local x1):
  -> CONCURRENT: neither caused the other (a scalar
     Lamport clock would hide this, only a vector shows it)
```

If `a` happens-before `b`, then `L(a) < L(b)` — but the converse is false, which is
exactly why vector clocks exist: they declare two events **concurrent** when neither
vector dominates the other.

## 3. Replication & quorums: killing the stale read

To survive a crash you keep copies. Primary/backup replication sends all writes to a
primary that forwards to backups — but replication takes time, so a read off a *lagging*
backup is **stale**. [`03_replication.c`](03_replication.c) (`make run3`) shows the bug
on 3 replicas, then fixes it with quorums where **R + W > N**:

```
make run3
```
```
=== STALE READ: a client reads only R2 (R=1) ===
  read R2 -> value=10 (v1)  <- STALE: the latest write was 20
  With R=1 and W=2 on N=3: R+W = 3, NOT > N. A read quorum {R2} can miss
  the write quorum {R0,R1} entirely. No overlap => staleness is possible.

=== QUORUM FIX: R=2, W=2, N=3  (R+W=4 > 3) ===
  read {R1,R2} -> pick highest version -> value=20 (v2)
```

Because any read set of size R and any write set of size W must **overlap** when
R + W > N, every read is guaranteed to see at least one replica that holds the latest
write — so it reads the newest version. Tuning R and W is how systems trade strong
consistency against availability and latency.

## 4. Raft-lite: leader election & log replication

Consensus is a cluster agreeing on one ordered log despite failures.
[`04_raft_lite.c`](04_raft_lite.c) (`make run4`) is a deterministic simulation of Raft's
two core mechanisms on a 5-node cluster (majority = 3): a **term-based majority
election**, **commit-on-majority** replication, and **re-election** after the leader
crashes. (See the honesty note above for what it deliberately omits.)

```
make run4
```
```
=== 1. Leader election (term 1) ===
     => node 0 WINS with 5/5 votes (majority is 3) -> LEADER term 1

=== 2. Log replication & commit-on-majority ===
  -- leader 0 replicates entry: "SET x = 42" --
     => 5/5 stored >= majority 3: entry COMMITTED at index 1

=== 3. The leader CRASHES ===
  node 0 (leader) goes DOWN. Followers stop hearing heartbeats and will
  time out, starting a new election in a HIGHER term.

=== 4. Re-election in a new term (term 2) ===
  -- election for term 2, candidate = node 1 --
     node 0 is DOWN, cannot vote
     => node 1 WINS with 4/5 votes (majority is 3) -> LEADER term 2
  -- leader 1 replicates entry: "SET y = 7" --
     => 4/5 stored >= majority 3: entry COMMITTED at index 2
```

The three ideas that make this safe: **terms + one vote per term + majority** mean at
most one leader can exist per term; an entry is **committed only once a majority store
it**, so it survives any minority failure; and on a leader crash a follower **times out
and wins a new term**, so the cluster self-heals as long as a majority is alive.

---

## 5. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`.

### Exercise 42.1 — Majority / quorum check  (`make ex1`)
Implement `is_majority(votes, n)` (a strict majority is `votes > n/2`) in
[`exercises/ex1_is_majority.c`](exercises/ex1_is_majority.c) and use it in an election
tally. Expected (`make sol1`):
```
is_majority(votes=3, n=5) = 1
is_majority(votes=2, n=5) = 0
is_majority(votes=3, n=4) = 1
is_majority(votes=2, n=4) = 0
is_majority(votes=2, n=3) = 1
is_majority(votes=1, n=3) = 0
is_majority(votes=1, n=1) = 1

tally: 3/5 YES -> ELECTED (majority)
```

### Exercise 42.2 — Lamport clock update  (`make ex2`)
Implement `lamport_tick` (local/send) and `lamport_recv` (`max(local,incoming)+1`) in
[`exercises/ex2_lamport_update.c`](exercises/ex2_lamport_update.c) and order a 2-node
event set. Expected (`make sol2`):
```
a  P0 local       L0=1
b  P0 send m      L0=2 (m=2)
c  P1 local       L1=1
d  P1 recv m      L1=3

ordering by Lamport timestamp: a(1) < b(2), c(1) < d(3)
causal edge b -> d holds: L(b)=2 < L(d)=3
```

### Exercise 42.3 — Quorum read  (`make ex3`)
Implement `quorum_read` in [`exercises/ex3_quorum_read.c`](exercises/ex3_quorum_read.c):
read R replicas and return the value only if all R agree, else report no quorum.
Expected (`make sol3`):
```
A: R=2 over {20,20,10} -> quorum value = 20
B: R=2 over {20,10,20} -> no quorum
C: R=3 over 2 replicas -> no quorum
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **RPC delivery semantics** | A lost reply ≠ a lost request, so retries are mandatory; idempotency or request-id dedup makes them safe (at-least-once → at-most-once → "exactly-once") |
| **Timeouts & retries** | The only way a caller can react to silence on an unreliable network — every RPC layer is built on them |
| **Lamport clocks** | A single counter gives a causal total order with no shared clock; wall clocks can't, because they drift |
| **Vector clocks** | Detect *concurrency* (incomparable events) that a scalar Lamport clock hides — the basis of conflict detection |
| **Replication & stale reads** | Copies buy fault tolerance but open a consistency gap; a lagging replica serves old data |
| **Quorums (R + W > N)** | Overlapping read/write quorums guarantee a read sees the latest write; tuning R, W trades consistency vs availability |
| **Raft consensus** | Terms + one-vote-per-term + majority = a single leader; commit-on-majority + re-election make a replicated log survive crashes |

## Further reading

- **MIT 6.5840 (formerly 6.824) — Distributed Systems** (the course these concepts
  come from; builds RPC, replication, and a full Raft in Go — do the labs for the real
  thing): https://pdos.csail.mit.edu/6.824/
- **Raft paper — "In Search of an Understandable Consensus Algorithm"** (Ongaro &
  Ousterhout; the source for Demo 4, with the safety rules this simulation omits):
  https://raft.github.io/raft.pdf
- **"Designing Data-Intensive Applications"** (Martin Kleppmann; the definitive
  practitioner's book on replication, partitioning, consistency, and consensus):
  https://dataintensive.net/

**Next:** Module 43 — Security & Cryptography Foundations — see *why* vulnerabilities
exist one level below the applied White-Hat track: a buffer overrun into its neighbour,
a format string as a write primitive, an integer overflow into a tiny allocation, and
the crypto primitives (XOR, a hash, constant-time compare) under Module 18. →
[../43_security/README.md](../43_security/README.md)
