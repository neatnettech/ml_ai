# Module 37 — Concurrency

**Purpose:** Modern machines run many things at once — multiple cores, multiple
threads inside one process, all sharing the same memory. That sharing is where
the power *and* the bugs come from. This module makes the core concurrency ideas
concrete in C with POSIX threads: you'll spawn threads and join them, *watch* a
data race lose updates, then fix it three ways (mutex, condition variable,
atomics), and see how a deadlock arises and how a lock ordering prevents it.
These are the mechanics every server, kernel, and database is built on.

**Prerequisites:** Module 30 (C, pointers — you pass `void *` arguments and cast
them back). Module 36 (the OS view: processes, scheduling) is helpful for
*why* threads interleave the way they do, but is not required.

**What you'll learn:**
- **Threads:** how to `pthread_create` N workers, give each its own argument, and
  `pthread_join` to collect results — real parallelism on multiple cores
- **Data races:** why `counter++` is not atomic, and how concurrent threads
  silently *lose updates* so the answer comes out wrong and non-deterministic
- **Mutual exclusion:** a `pthread_mutex_t` makes a *critical section* run
  uninterrupted — correct, at the cost of serializing the work
- **Condition variables:** `pthread_cond_wait`/`signal` let threads sleep until a
  condition holds (a bounded-buffer producer/consumer) — no busy-waiting
- **Atomics:** C11 `atomic_long` + `atomic_fetch_add` give a lock-free counter —
  simpler than a mutex and often faster for a single shared value
- **Deadlock:** two locks taken in opposite order can hang forever; a consistent
  global lock ordering makes it impossible

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 37 runs **natively on Apple Silicon** — no container needed. macOS ships
POSIX threads (`<pthread.h>`) and C11 atomics (`<stdatomic.h>`) with the system
`clang`. You only need `clang` + `make` (Xcode Command Line Tools):

```bash
make run        # build + run all five demos
```

Threads require `-pthread` at compile and link time; it is already in the
Makefile's `CFLAGS`.

> The numbers below (timings, race values) are **real captured output** from an
> Apple Silicon Mac. The race demo is **non-deterministic** — your wrong value
> will differ from the one shown, and will change every run. That is the point.

---

## 1. Threads: spawn, run in parallel, join

A **thread** is an independent flow of execution that shares the process's
address space (globals, heap) with the other threads. [`01_threads.c`](01_threads.c)
spawns 4 workers, each summing a different slice of integers into its *own*
argument struct (no sharing → no race), then joins them and combines the results
(`make run1`):

```
=== Spawning 4 threads, each summing a slice ===
  thread 3 summed [3000000, 4000000) -> 3499999500000
  thread 2 summed [2000000, 3000000) -> 2499999500000
  thread 1 summed [1000000, 2000000) -> 1499999500000
  thread 0 summed [0, 1000000) -> 499999500000

  combined total = 7999998000000
  expected       = 7999998000000  (match)
```

Two things to notice: the threads finish in an **arbitrary order** (here 3,2,1,0
— the scheduler decides), and `pthread_join` is what makes it safe to read each
worker's result. This is the clean pattern: split work into independent pieces,
no shared mutable state.

## 2. The data race (the teaching bug)

Now make all the threads touch the **same** variable. [`02_race.c`](02_race.c) has
8 threads each do `counter++` a million times, with no synchronization. `counter++`
is really *load → add 1 → store*; when two threads interleave those steps, one
store overwrites the other and an update is **lost** (`make run2`):

```
=== 8 threads each do counter++ 1000000 times ===

  final counter = 2195055
  expected      = 8000000
  lost updates  = 5804945  (RACE: updates lost)
```

Run it again and you get a *different* wrong answer — this is non-deterministic:

```
  final counter = 1019385
  expected      = 8000000
  lost updates  = 6980615  (RACE: updates lost)
```

The expected total is 8,000,000; we lost ~73% of the updates the second run. This
is a **data race**: concurrent unsynchronized access to a shared location where at
least one access is a write. It is the central bug this module teaches you to
prevent.

## 3. Fix #1 — a mutex (mutual exclusion)

[`03_mutex.c`](03_mutex.c) wraps the increment in a `pthread_mutex_t`.
`pthread_mutex_lock` blocks until this thread is the *sole* owner; the
load-add-store now runs as an uninterruptible **critical section**;
`pthread_mutex_unlock` lets the next thread in. Correct every single run
(`make run3`):

```
=== 8 threads, counter++ 1000000 times each, GUARDED by a mutex ===

  final counter = 8000000
  expected      = 8000000  (correct)
```

The cost: the lock **serializes** the increments, so all that parallelism is gone
for the guarded part — this is noticeably slower than the unsynchronized version.
A mutex buys correctness with throughput; keep critical sections small.

## 4. Condition variables — a bounded-buffer producer/consumer

A mutex alone can't express "wait until there's room" or "wait until there's
data." A **condition variable** can: `pthread_cond_wait` atomically releases the
mutex and sleeps until another thread calls `pthread_cond_signal` — no spinning,
no wasted CPU. [`04_condvar.c`](04_condvar.c) is a classic bounded buffer (capacity
4): a producer blocks when full, a consumer blocks when empty (`make run4`):

```
=== Bounded buffer (cap 4): 1 producer, 1 consumer, 16 items ===
  produced  0   (buffer now holds 1)
  produced  1   (buffer now holds 2)
  produced  2   (buffer now holds 3)
  produced  3   (buffer now holds 4)
           consumed  0   (buffer now holds 3)
           consumed  1   (buffer now holds 2)
           consumed  2   (buffer now holds 1)
           consumed  3   (buffer now holds 0)
  produced  4   (buffer now holds 1)
  ...
           consumed 15   (buffer now holds 0)

  consumer received all 16 items, sum = 120 (expected 120)

  Done — no busy-waiting: idle threads slept on a condition var.
```

The buffer never exceeds its capacity of 4. **The golden rule:** always wait
inside a `while (condition)` loop, never a plain `if` — a thread can wake
spuriously or lose its slot to another waiter, so it must re-check the predicate
after every wake.

## 5. Fix #2 — C11 atomics (lock-free)

[`05_atomics.c`](05_atomics.c) fixes the demo-2 race a third way: make the counter
an `atomic_long` and increment with `atomic_fetch_add`. The hardware performs the
read-modify-write as **one indivisible operation**, so no update can be lost —
with no mutex at all (`make run5`):

```
=== 8 threads, atomic_fetch_add 1000000 times each (lock-free) ===

  final counter = 8000000
  expected      = 8000000  (correct)
```

Versus the mutex: the code is simpler (no lock to acquire, hold, and remember to
release; no deadlock risk), and for a single counter it is usually faster since
there is no blocking. Atomics shine for small lock-free ops on **one** variable;
reach for a mutex once a critical section must update **several** variables
together as a unit.

---

## 6. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`.

### Exercise 37.1 — Parallel array sum  (`make ex1`)
Implement the two TODOs in [`exercises/ex1_parallel_sum.c`](exercises/ex1_parallel_sum.c):
each thread sums one slice; main joins them and combines. Verify it matches the
serial sum. Expected (`make sol1`):
```
serial sum   = 99000000
parallel sum = 99000000
match        = yes
```
(The unfinished stub prints `parallel sum = 0` / `match = NO` until you fill it in.)

### Exercise 37.2 — Fix a racy counter  (`make ex2`)
[`exercises/ex2_fix_race.c`](exercises/ex2_fix_race.c) ships *with* the demo-2 race.
Fix it with **either** a mutex (demo 3) **or** an atomic (demo 5). The stub shows
the bug; the solution uses the atomic fix:
```
# make ex2 (unfixed) -> wrong, e.g.:
final counter = 1049382
expected      = 4000000
correct       = NO (race not fixed)

# make sol2 (fixed):
final counter = 4000000
expected      = 4000000
correct       = yes
```

### Exercise 37.3 — Deadlock and its fix  (`make ex3`)
[`exercises/ex3_deadlock.c`](exercises/ex3_deadlock.c) has two mutexes A and B and
two threads. A **deadlock** occurs when each thread holds one lock and waits for
the other forever:

```
thread 1: lock(A); lock(B); ...      thread 2: lock(B); lock(A); ...
```

If thread 1 grabs A while thread 2 grabs B, thread 1 waits forever for B and
thread 2 waits forever for A — the program **hangs with no output and no exit**;
you would have to Ctrl-C it.

**The fix is a consistent global lock ordering:** if *every* thread always locks A
before B, no wait cycle can form. The exercise asks you to make `worker_two` lock
A-before-B like `worker_one`. Both the exercise stub and the solution run to
completion (`make ex3` / `make sol3`):
```
=== Two mutexes, two threads — consistent A-before-B ordering ===
  worker_one: locked A then B, does its work
  worker_two: locked A then B, does its work

  Both threads finished — no deadlock (consistent A-before-B order).
```

**How the default build is kept from hanging.** The committed `make ex3` is safe
by construction — the real, hanging deadlock is gated behind a `-DDEADLOCK`
compile flag (never passed by `make`). To *watch* the deadlock yourself:

```bash
clang -std=c11 -pthread -DDEADLOCK -o /tmp/dl exercises/ex3_deadlock.c
/tmp/dl          # hangs forever — press Ctrl-C
```

That build gives the two threads the opposite lock orders and a tiny `usleep`
between the two locks to widen the interleave window, so the hang is reliable.
Without the flag, the orders are consistent and it always terminates.

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **Threads & join** | `pthread_create`/`pthread_join` give real parallelism; per-thread arg structs avoid sharing — the clean way to split work |
| **Data race** | Unsynchronized shared writes lose updates non-deterministically; `counter++` is load-add-store, not atomic |
| **Mutex** | A lock makes a critical section uninterruptible — correct, but it serializes and costs throughput |
| **Condition variable** | Wait/signal lets threads sleep until a predicate holds (producer/consumer) with no busy-waiting; always wait in a `while` loop |
| **Atomics** | `atomic_fetch_add` is a lock-free indivisible read-modify-write — simplest fix for a single shared value |
| **Deadlock** | Opposite lock orders create a wait cycle that hangs forever; a consistent global lock ordering prevents it |

## Further reading

- **CS:APP3e, Chapter 12 — Concurrent Programming** (threads, races, mutexes,
  semaphores, deadlock — pairs with this module 1:1): http://csapp.cs.cmu.edu/
- **OSTEP — Concurrency** (the free Operating Systems: Three Easy Pieces; the
  locks / condition variables / semaphores chapters are the best intuitive
  treatment): https://pages.cs.wisc.edu/~remzi/OSTEP/
- **The Little Book of Semaphores** (Downey — a build-up of classic
  synchronization puzzles, free PDF):
  https://greenteapress.com/wp/semaphores/

**Next:** Module 38 — Algorithms & Data Structures — asymptotics, sorting,
hashing, trees/heaps, graphs, and dynamic programming in C (bridging to the Pure
ML track). *(Not yet built — see [the track plan](../cs-foundations-track.md).)*
See [../38_algorithms/README.md](../38_algorithms/README.md).
