# Module 33 — Computer Architecture

**Purpose:** You've written C (Modules 30–31) and read the assembly it compiles to
(Module 32). Now find out why two programs that do the *exact same arithmetic* can
differ in speed by 10–80×. The answer is the machine underneath: a **pipelined** CPU
that guesses which way branches go, and a **memory hierarchy** of caches that reward
code touching memory in the right order. This module makes those invisible structures
*measurable* — every claim is a timing experiment you run yourself in portable C.

**Prerequisites:** Module 32 (Assembly) — or at least Module 31 (C II). You should be
comfortable reading C, running `make`, and the idea that source compiles to machine
instructions a CPU executes.

> **A word on numbers:** the absolute times below come from one Apple Silicon laptop
> and **will not match yours** — they depend on your CPU, cache sizes, and what else is
> running. That's fine. The *ratios* and the *shapes* (row-major faster, sorted faster,
> a latency staircase) are the lesson, and they reproduce on essentially any modern CPU.

**What you'll learn:**
- **Spatial locality**: why row-major beats column-major, and what a *cache line* is
- How to **measure the cache line size** from a stride experiment
- **Branch prediction**: why a sorted array is far faster to filter than a shuffled one,
  and how the compiler can erase the effect at `-O2`
- The **memory hierarchy** (L1 → L2 → LLC → DRAM) read straight off a latency staircase

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 33 runs **natively on Apple Silicon (arm64)** — no container needed. You only
need `clang` + `make` (Xcode Command Line Tools):

```bash
make run                              # build + run all four demos
```

Everything is built at **`-O2`** so the timings reflect optimized code (timing a debug
build teaches you nothing about real performance). Because the optimizer will happily
*delete* a loop whose result is unused, every measured loop writes its result to a
`volatile` sink — and demo 3 goes further to stop the compiler erasing the very branch
it studies (see §3).

---

## 1. Spatial locality: row-major vs column-major

A C 2D array is stored **row-major** — `a[i][0], a[i][1], …` are contiguous. The CPU
never fetches one int; it pulls a whole **cache line** (~64 bytes = 16 ints) at a time.
Summing along rows uses every int in each fetched line; summing down columns jumps a
full row between accesses, wasting almost the whole line.
[`01_locality.c`](01_locality.c), `make run1`:

```
Array: 4096 x 4096 ints  (64 MiB)
  row-major sum   : 0.0017 s   (sum=58720256)
  column-major sum: 0.1454 s   (sum=58720256)
  ratio (col / row): 84.14x slower column-major
```

Same 16.7M additions, same sum — only the **access order** changed, and it cost 84×.
This is the single most important performance idea in the module: *touch memory in the
order it's laid out.*

## 2. Measuring the cache line size with stride

If a cache line is ~64 bytes, then touching memory every 16 bytes still rides lines you
already paid for, but touching every 128 bytes needs a fresh line each time.
[`02_stride.c`](02_stride.c) keeps the touch *count* fixed and varies the *stride*,
printing nanoseconds per access (`make run2`):

```
Array 64 MiB, 16777216 touches per run.
  stride(bytes)   ns/access
  -------------   ---------
          4           0.76
          8           0.66
         16           0.60
         32           0.57
         64           0.77
        128           2.53
        256           2.78
```

Cost stays flat (~0.6 ns) up through stride 64, then **jumps ~3–4×** at stride 128 and
plateaus. The elbow marks where each access needs its own line. On this machine it lands
between 64 and 128 bytes: the L1 line is 64 B, but the prefetcher pulls a 128 B pair, so
the cost doesn't fully bite until 128 B. The *takeaway* — a cache line is tens of bytes,
not one — is exactly right; the precise elbow is your hardware's signature.

## 3. Branch prediction: sorted vs unsorted

A pipelined CPU starts executing instructions *after* a branch before it knows the
outcome, by **predicting** it. A correct prediction is free; a **misprediction** flushes
the wrongly-fetched work and restarts — ~15–20 wasted cycles.
[`03_branch_prediction.c`](03_branch_prediction.c) sums elements `>= 128` over an array
of random bytes (0–255), once **shuffled** and once **sorted** (`make run3`):

```
4194304 elements, 64 repeats, threshold 128.
  unsorted: 0.7521 s   (sum=25693071040)
  sorted  : 0.0744 s   (sum=25693071040)
  ratio (unsorted / sorted): 10.11x slower when unpredictable
```

Sorted is **~10× faster**. The data and the work are identical; only the *order* differs.
Sorted, the `if (data[i] >= 128)` branch goes false…false…then true…true — one switch the
predictor nails. Shuffled, it's a coin flip the predictor can't learn, so it mispredicts
~half the time and flushes the pipeline on each miss.

> **The compiler can erase this effect.** At `-O2`, clang first compiled the `if` into a
> *branchless* conditional-select plus NEON SIMD reduction — no branch, so sorted and
> unsorted ran the *same* speed (~1.3×, not 10×). That is itself an architecture lesson:
> the best fix for an unpredictable branch is to have *no branch*. To actually observe
> prediction we force a real data-dependent branch with `#pragma clang loop
> vectorize(disable)` and a compiler barrier on the taken path. Remove those two lines
> and re-time to watch the compiler defeat the experiment.

## 4. The memory hierarchy, one latency staircase

Memory is a hierarchy: small/fast caches near the core, big/slow DRAM far away.
[`04_memory_hierarchy.c`](04_memory_hierarchy.c) **pointer-chases** a random cycle
through buffers of growing size. Each hop (`idx = a[idx]`) depends on the previous one,
so the prefetcher can't run ahead — every access pays the true latency of wherever that
buffer lives. Sweep the size and read the steps (`make run4`):

```
Pointer-chase latency vs working-set size.
  size       ns/access
  --------   ---------
     4 KiB       1.19
    16 KiB       1.01
    64 KiB       1.00
   128 KiB       0.99
   256 KiB       4.31     <- spills out of L1
   512 KiB       5.34
     1 MiB       6.35
     2 MiB       6.74
     4 MiB       8.22
     8 MiB       9.40
    16 MiB      11.98
    32 MiB      54.79     <- spills out of cache into DRAM
```

The **flat regions are cache levels**: ~1 ns while the working set fits in L1, a step up
to ~4–6 ns in L2, a gentle climb through the last-level cache, then a **cliff to ~55 ns**
at 32 MiB when the data no longer fits in any cache and every hop hits DRAM. You are
reading this machine's L1/L2/LLC sizes directly off the timings — and the ~50× span from
L1 to DRAM is *why* locality (§1) matters so much.

---

## 5. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`. (Until you fill
a TODO in, the stub prints `0.00` — that's expected.)

### Exercise 33.1 — Estimate your cache line size  (`make ex1`)
Fill in the timed loop in [`exercises/ex1_cache_line.c`](exercises/ex1_cache_line.c) so
it does `TOUCHES` strided accesses, then read the elbow off the table. Expected shape
(`make sol1`):
```
  stride(bytes)   ns/access
  -------------   ---------
          4           0.60
         64           0.83
        128           2.71     <- cost jumps here: line size is in this range
        256           2.82
```

### Exercise 33.2 — Sorted-vs-unsorted speedup  (`make ex2`)
Time `sum_above` over a shuffled array and a sorted copy in
[`exercises/ex2_branch_speedup.c`](exercises/ex2_branch_speedup.c), then report the
speedup. Expected (`make sol2`):
```
  unsorted: 0.7656 s
  sorted  : 0.0732 s
  speedup (unsorted / sorted): 10.46x
```

### Exercise 33.3 — Matmul loop order: ijk vs ikj  (`make ex3`)
Implement both loop orders in
[`exercises/ex3_matmul_order.c`](exercises/ex3_matmul_order.c) and explain why ikj wins.
Expected (`make sol3`):
```
512x512 double matmul:
  ijk: 0.1413 s
  ikj: 0.0184 s
  speedup (ijk / ikj): 7.68x
```
**Why:** with `k` as the middle loop, the inner `j`-loop sweeps `B[k][j]` and `C[i][j]`
across rows (stride 1) while `A[i][k]` is constant — every inner step rides the cache
line just fetched. In `ijk` the inner `k`-loop walks `B[k][j]` *down a column* (stride
N), missing the cache on nearly every access. Same FLOPs, ~8× the speed.

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **Spatial locality / cache lines** | The CPU fetches ~64 B at a time; touch memory in layout order or pay 10–80× (row vs column) |
| **Stride & line size** | Cost flattens once each access needs its own line — the elbow reveals the line size |
| **Branch prediction** | Unpredictable branches flush the pipeline (~10× here); sorted/predictable data is far faster |
| **Compiler vs branches** | At `-O2` the compiler may make a branch *branchless* — sometimes the real fix is no branch at all |
| **Memory hierarchy** | L1→L2→LLC→DRAM is a latency staircase (~1 ns to ~55 ns here); the cliff is why locality pays |
| **Loop order (matmul)** | Same arithmetic, different inner-loop stride → ikj beats ijk several-fold purely on locality |

## Further reading

- **CS:APP3e, Chapters 5–6 — Optimizing Program Performance & The Memory Hierarchy**
  (the definitive treatment; this module is its lab in miniature): http://csapp.cs.cmu.edu/
- **CS:APP Cache Lab** (write a cache simulator, then optimize a matrix transpose for
  locality — the natural next step after Exercise 33.3): http://csapp.cs.cmu.edu/
- **MIT 6.191 (formerly 6.004) Computation Structures** (pipelining, hazards, and caches
  from the hardware side): https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/
- **What Every Programmer Should Know About Memory** (Ulrich Drepper — the deep, complete
  reference on caches, prefetching, and NUMA): https://www.akkadia.org/drepper/cpumemory.pdf

**Next:** Module 34 — Linking, Loading & Processes — what turns your compiled `.o` files
into a running program: symbol resolution, relocation, the loader, and the process address
space. *(Not yet built — see [the track plan](../cs-foundations-track.md).)*
→ [../34_linking_loading/README.md](../34_linking_loading/README.md)
