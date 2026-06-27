# Module 39 — Advanced Algorithms

**Purpose:** Module 38 gave you the working toolkit — sorting, hashing, trees, graphs, DP.
This module steps up to the *design discipline* behind them: the great algorithmic
**paradigms** (divide & conquer, greedy, graph optimization, network flow) and the wall
they all eventually hit (**NP-hardness**). The point here is not just "here is an
algorithm" but **why it is correct and how fast it is** — exchange arguments, cut and
flow properties, the max-flow min-cut theorem, and an honest account of P vs NP and
approximation. This is the MIT 6.1220 (6.046) layer of the CS Foundations track, in real C.

**Prerequisites:** **Module 38 — Algorithms & Data Structures** (asymptotics / big-O,
graphs as adjacency lists, heaps, recursion). We reuse those without re-deriving them.

**What you'll learn:**
- **Divide & conquer** beyond merge sort: counting inversions in `O(n log n)`, and *seeing*
  it beat the `O(n^2)` brute force on the clock
- **Greedy** + the **exchange argument** that proves the greedy choice is optimal (interval scheduling)
- **Dijkstra** with a real binary-heap priority queue, why the settled distance is final,
  and when you must fall back to **Bellman-Ford**
- **Minimum spanning trees** via **Kruskal + union-find**, justified by the **cut property**
- **Maximum flow** via **Edmonds-Karp**, and the **max-flow min-cut** duality
- **NP-hardness** for real: brute force vs a provable **2-approximation**, and what P vs NP actually claims

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 39 runs **natively on Apple Silicon** — no container needed. You only need
`clang` + `make` (Xcode Command Line Tools):

```bash
make run                              # build + run all six demos
```

Everything is portable C11 (`-std=c11 -Wall -Wextra -Wpedantic -O2`, zero warnings) and
frees all heap memory. No architecture-specific code.

---

## 1. Divide & conquer — counting inversions

**Divide & conquer** solves a problem by splitting it into independent subproblems,
solving each recursively, and *combining* the answers. The art is in the combine step.
[`01_divide_conquer.c`](01_divide_conquer.c) counts **inversions** — pairs `(i, j)` with
`i < j` but `a[i] > a[j]` (how far the array is from sorted). The naive method checks all
`C(n,2)` pairs in `O(n^2)`. The trick: piggyback on merge sort. When merging two sorted
halves, the moment you take an element from the *right* half ahead of `k` elements still
left in the *left* half, those are exactly `k` inversions — count them for free.

```
make run1
```
```
  array: 2 4 1 3 5
  inversions (pairs out of order): (2,1) (4,1) (4,3)
  naive = 3, divide&conquer = 3  -> AGREE

  n = 20000 random ints
  naive          = 100276998   (0.032 s)
  divide&conquer = 100276998   (0.0007 s)
  -> same answer, and D&C is ~46x faster here
```

**Why it's correct:** every inversion `(i, j)` has its two elements end up in *different*
halves at exactly one level of the recursion (the level where the split falls between
them) — or in the same half, where a recursive call counts it. The merge counts every
cross-half inversion exactly once, so the three terms partition all inversions with no
double counting.

**Complexity:** the recurrence is `T(n) = 2T(n/2) + O(n)`, which by the **master theorem**
is `O(n log n)` — versus `O(n^2)` naive. The measured ~46x speedup at `n = 20000` is that
gap made visible (it widens as `n` grows).

## 2. Greedy — interval scheduling

A **greedy** algorithm builds a solution by repeatedly making the choice that looks best
*right now*, never reconsidering. Greedy is fast and simple — but only *correct* for
problems with the right structure, and you must **prove** it. [`02_greedy.c`](02_greedy.c)
solves **interval scheduling** (activity selection): given activities with start/finish
times and one room, schedule as many non-overlapping activities as possible. The rule:
sort by **finish time**, then repeatedly take the earliest-finishing activity that still
fits.

```
make run2
```
```
  sorted by finish time, then greedily take earliest-finishing that fits:
    take id 1  [1,4)
    take id 4  [5,7)
    take id 8  [8,11)
    take id 11  [12,16)

  chosen 4 activities: 1 4 8 11
```

**Why "earliest finish" is optimal (exchange argument):** let greedy's first pick be `g`
(earliest finish of all). Take *any* optimal schedule and let its first activity be `o`.
Since `g` finishes no later than `o`, replacing `o` with `g` cannot collide with anything
later in that optimal schedule — so we get another optimal schedule that *starts with the
greedy choice*. Now recurse on the activities that start after `g` finishes. By induction
the greedy choice is always extendable to an optimum, so greedy *is* an optimum. Note the
proof tells you the right key: greedy on *shortest duration* or *fewest conflicts* would
**not** be optimal. **Complexity:** `O(n log n)` for the sort, then a single `O(n)` sweep.

## 3. Shortest paths — Dijkstra with a binary heap

[`03_shortest_paths.c`](03_shortest_paths.c) runs **Dijkstra** from a source on a weighted
graph with **non-negative** edges. Keep a tentative distance to each vertex; repeatedly
extract the unsettled vertex with the smallest tentative distance (a **binary min-heap**
with `decrease-key`), settle it, and **relax** its edges:
`dist[w] = min(dist[w], dist[u] + w(u,w))`.

```
make run3
```
```
  shortest distance from A to each vertex:
    A -> A : 0
    A -> B : 7
    A -> C : 9
    A -> D : 20
    A -> E : 20
    A -> F : 11
```

**Why the settled distance is final:** when we extract `u` with the minimum tentative
distance, consider any other path to `u`. It must leave the already-settled set at some
vertex `x` whose tentative distance is `>= dist[u]` (else we'd have extracted `x` first),
then travel a **non-negative** remainder — so it cannot beat `dist[u]`. Hence `dist[u]` is
optimal at extraction. That argument **breaks** if edges can be negative (a later cheap
edge could undercut a settled vertex), which is why you then need **Bellman-Ford**:
`O(V·E)`, relaxing every edge `V−1` times, and it also **detects negative cycles**.
**Complexity:** with a binary heap, `O((V + E) log V)`.

## 4. Minimum spanning tree — Kruskal + union-find

[`04_mst.c`](04_mst.c) finds a **minimum spanning tree** (the cheapest set of `n−1` edges
connecting all `n` vertices, no cycle) with **Kruskal**: sort edges ascending, then add
each edge iff its endpoints are in *different* components (else it would close a cycle).
The component test is a **disjoint-set (union-find)** with **union by rank + path
compression**.

```
make run4
```
```
    add C-E (w= 5)
    add A-D (w= 5)
    add D-F (w= 6)
    add A-B (w= 7)
    add B-E (w= 7)
    skip B-C (w= 8) -- would make a cycle
    skip E-F (w= 8) -- would make a cycle
    skip B-D (w= 9) -- would make a cycle
    add E-G (w= 9)

  MST has 6 edges, total weight = 39
```

**Why it's correct (cut property):** for *any* partition of the vertices into two
non-empty sets, the minimum-weight edge crossing that partition belongs to *some* MST.
Each edge Kruskal adds is, at that moment, the cheapest edge crossing the cut between the
component it grows and the rest — a *safe* edge — so the final tree is an MST. **Why
union-find is fast:** `find` flattens the tree it walks (path compression) and `union`
hangs the shorter tree under the taller (union by rank); together, `m` operations cost
`O(m · α(n))`, where `α` (inverse Ackermann) is `<= 4` for any conceivable `n`. **Overall:**
`O(E log E)` dominated by the sort.

## 5. Maximum flow — Edmonds-Karp, and min-cut

[`05_max_flow.c`](05_max_flow.c) computes **max flow** from source to sink in a capacitated
network via **Edmonds-Karp** (Ford-Fulkerson where each augmenting path is found by BFS).
Repeatedly find a path in the **residual graph** (leftover capacity plus back-edges that
let you *cancel* earlier flow) and push its bottleneck.

```
make run5
```
```
    augmenting path found, pushed 12 unit(s)  (total 12)
    augmenting path found, pushed 4 unit(s)  (total 16)
    augmenting path found, pushed 7 unit(s)  (total 23)

  MAX FLOW value = 23
  min cut: source side = {S,1,2,4}  (its capacity equals the max flow, by max-flow min-cut)
```

**Max-flow min-cut theorem:** the maximum flow value equals the minimum capacity of any
`s`–`t` **cut** (a split of the vertices with `s` on one side, `t` on the other; its
capacity is the total capacity of edges crossing forward). When BFS can no longer reach
`t` in the residual graph, the vertices still reachable from `s` are exactly the
minimum-cut side — and the current flow equals that cut's capacity, so it is provably
maximal. The demo prints that side `{S,1,2,4}`; its forward capacity (`1->3` =12, `4->T`
=4, `4->3` =7) sums to 23, matching the flow. **Why BFS (Edmonds-Karp):** choosing the
*shortest* augmenting path bounds the algorithm at `O(V·E^2)` and guarantees termination
even with irrational capacities (plain Ford-Fulkerson can stall).

## 6. NP-hardness — vertex cover, exact vs 2-approximation

[`06_np_hardness.c`](06_np_hardness.c) is about the wall. A **vertex cover** is a set of
vertices touching every edge; **minimum** vertex cover is **NP-complete** — no known
polynomial algorithm, and one would imply **P = NP**. The demo does both: **brute force**
(try all `2^n` subsets — exact but exponential) and a **2-approximation** (pick any
uncovered edge, add *both* endpoints, repeat — `O(E)`).

```
make run6
```
```
  triangle   n=3 m= 3 : optimal=2  approx=2  ratio=1.00  (approx <= 2*opt? yes)
  path-5     n=5 m= 4 : optimal=2  approx=4  ratio=2.00  (approx <= 2*opt? yes)
  star-5     n=5 m= 4 : optimal=1  approx=2  ratio=2.00  (approx <= 2*opt? yes)
  dense-6    n=6 m= 8 : optimal=4  approx=6  ratio=1.50  (approx <= 2*opt? yes)
```

**P vs NP, briefly and honestly.** **P** = problems solvable in polynomial time. **NP** =
problems whose *solutions are checkable* in polynomial time (given a cover, you can verify
it covers every edge fast). Every NP problem reduces to any **NP-complete** one, so a fast
algorithm for *one* NP-complete problem would solve *all* of NP fast (`P = NP`). Whether
`P = NP` is the famous open question; the consensus bet is **no**. We show NP-hardness by
**reduction** — vertex cover is NP-hard because the known-hard 3-SAT reduces to it.

**Why the 2-approximation is never worse than 2× optimal:** the edges it picks share no
vertex (taking both endpoints removes them from contention), so they form a **matching**.
Any valid cover must include at least one endpoint of each matched edge, so
`OPT >= (#picked edges)`; we used exactly `2 × (#picked edges)`. Hence `approx <= 2·OPT` —
exactly what the table confirms on every input. This is the honest deal with NP-hard
problems: give up *either* optimality (approximate), *or* speed (brute force / branch &
bound), *or* generality (special cases) — you cannot keep all three unless `P = NP`.

---

## 7. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`.

### Exercise 39.1 — Union-Find  (`make ex1`)
Implement `dsu_find` (path compression) and `dsu_union` (union by rank) in
[`exercises/ex1_union_find.c`](exercises/ex1_union_find.c). Expected (`make sol1`):
```
connected(0,2) = 1  (expect 1)
connected(0,3) = 0  (expect 0)
connected(3,4) = 1  (expect 1)
connected(4,5) = 0  (expect 0)
number of components = 3  (expect 3)
```

### Exercise 39.2 — Dijkstra  (`make ex2`)
Fill in the selection + relaxation core in
[`exercises/ex2_dijkstra.c`](exercises/ex2_dijkstra.c) (simple `O(V^2)` version on a given
adjacency matrix). Expected (`make sol2`):
```
shortest distances from A:
  A -> A : 0
  A -> B : 7
  A -> C : 9
  A -> D : 20
  A -> E : 20
  A -> F : 11
```

### Exercise 39.3 — Vertex-cover 2-approximation  (`make ex3`)
Implement `approx_vc` in
[`exercises/ex3_vertex_cover.c`](exercises/ex3_vertex_cover.c); the harness checks it is
`<=` 2× the brute-force optimum on several small graphs. Expected (`make sol3`):
```
vertex cover: approx vs exact (approx must be <= 2 * optimal)
  triangle  optimal=2 approx=2  (approx <= 2*opt? yes)
  path-5    optimal=2 approx=4  (approx <= 2*opt? yes)
  star-5    optimal=1 approx=2  (approx <= 2*opt? yes)
  dense-6   optimal=4 approx=6  (approx <= 2*opt? yes)
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **Divide & conquer** | Split / recurse / combine; the combine step counts inversions for free → `O(n log n)` beats `O(n^2)` measurably |
| **Greedy + exchange argument** | Greedy is only correct with proof; "earliest finish" is optimal for interval scheduling, "shortest" is not |
| **Dijkstra / Bellman-Ford** | Heap-based shortest paths in `O((V+E) log V)`; non-negativity makes settled distances final, else use Bellman-Ford |
| **MST: Kruskal + union-find** | Cut property makes cheapest-crossing edges safe; union-find tests components in near-`O(1)` (`α(n) <= 4`) |
| **Max flow + min cut** | Augment along residual paths; max flow = min cut, and BFS (Edmonds-Karp) bounds it at `O(V·E^2)` |
| **NP-hardness & approximation** | P vs NP, reductions, and the honest trade: approximate, brute-force, or specialize — a 2-approx is provably `<= 2·OPT` |

## Further reading

- **CLRS — *Introduction to Algorithms*, 4th ed.** (the spine for this whole module:
  greedy & MST ch.15–21, shortest paths ch.22–24, max flow ch.24, NP-completeness &
  approximation ch.34–35): https://mitpress.mit.edu/9780262046305/introduction-to-algorithms/
- **MIT 6.1220 / 6.046 — Design and Analysis of Algorithms** (the course this module
  follows; lecture videos + notes on OCW): https://ocw.mit.edu/
- **Kleinberg & Tardos — *Algorithm Design*** (the clearest treatment of greedy exchange
  arguments, flow, and NP-completeness reductions): https://www.pearson.com/
- **Optional history:** Cook (1971) "The Complexity of Theorem-Proving Procedures" — the
  paper that started NP-completeness — and Karp (1972)'s 21 NP-complete problems.

**Next:** Module 40 — Compilers & Language Engineering — lexer → parser → AST → codegen,
building a small interpreter/compiler (Crafting Interpreters; Nand2Tetris 6–11; MIT
6.035). *(Not yet built — see [the track plan](../cs-foundations-track.md).)*
→ [../40_compilers/README.md](../40_compilers/README.md)
