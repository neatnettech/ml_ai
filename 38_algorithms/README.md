# Module 38 — Algorithms & Data Structures

**Purpose:** An algorithm is a recipe; a data structure is how you hold the data so
the recipe runs fast. This module is **the working toolkit — sorting, searching,
hashing, trees/heaps, graphs, and dynamic programming, implemented and *timed* in
C** so the difference between O(n²) and O(n log n) is something you watch happen
rather than memorize. It is also the **bridge into the Pure ML track's algorithmic
thinking**: the Python ML modules (gradient descent, k-NN, decision trees, the
attention/transformer modules) all rest on exactly these primitives — sorting and
heaps inside k-NN, hash maps inside tokenizers, graph traversal inside
autograd/computation graphs, and DP inside sequence alignment and Viterbi-style
decoding. Learn the costs here in C, and the Python later reads as "the same ideas
with the bookkeeping hidden."

**Prerequisites:** Module 30 (C programming I — pointers, dynamic memory). You will
`malloc`/`free` linked lists, trees, and tables throughout; if `Node *next` and
`free()` are not yet comfortable, do Module 30 first.

**What you'll learn:**
- **Asymptotics you can see:** time three sorts on growing `n` and watch the
  quadratic curve pull away from the n log n ones
- **Searching:** linear vs binary, why binary *demands* sorted input, counted in
  comparisons
- **Hashing:** a hash table with separate chaining, a string hash, and why
  lookups are *average* O(1)
- **Trees & heaps:** a binary search tree (ordered, in-order = sorted) and a binary
  min-heap / priority queue (push & pop-min in O(log n))
- **Graphs:** adjacency lists with BFS and DFS traversals
- **Dynamic programming:** memoization collapsing exponential recursion to linear,
  plus a real DP (0/1 knapsack), with the call-count blowup printed

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 38 runs **natively on Apple Silicon** — no container needed. You only need
`clang` + `make` (Xcode Command Line Tools):

```bash
make run        # build + run all six demos
```

Builds are `clang -std=c11 -Wall -Wextra -Wpedantic -g -O2` with **zero warnings**.
`-O2` matters here: the sorting demo's timings only mean something with the
optimizer on (we feed results to a `volatile` sink so the work isn't deleted).

---

## 1. Sorting & asymptotics

[`01_sorting.c`](01_sorting.c) (`make run1`) sorts the *same* random array three
ways at each size and times it. Insertion sort is **O(n²)**; merge sort and
quicksort are **O(n log n)**. The point is the *shape*: as `n` doubles, insertion's
time roughly quadruples while the others a bit more than double.

```
make run1
```
```
         n |    insertion |        merge |        quick
-----------+--------------+--------------+--------------
      1000 |       0.23 ms |       0.04 ms |       0.04 ms
      2000 |       0.92 ms |       0.08 ms |       0.09 ms
      4000 |       1.33 ms |       0.13 ms |       0.13 ms
      8000 |       5.07 ms |       0.29 ms |       0.30 ms
     16000 |      20.03 ms |       0.56 ms |       0.59 ms
     32000 |      80.59 ms |       1.19 ms |       1.29 ms
```

(Exact numbers vary by machine and run.) From 8000→16000→32000, insertion goes
5 → 20 → 80 ms — a clean **×4 per doubling**, the signature of n². Merge/quick go
0.3 → 0.6 → 1.3 ms — about **×2**, the signature of n log n. Quicksort uses a
median-of-three pivot so sorted input doesn't trigger its O(n²) worst case.

## 2. Linear vs binary search

[`02_searching.c`](02_searching.c) (`make run2`) searches a sorted array of 1000
and **counts comparisons**. Linear search is O(n); binary search halves the range
each step, O(log n) — but it is only correct on **sorted** input.

```
make run2
```
```
  target |    linear cmps |    binary cmps
---------+----------------+----------------
       1 |              1 |             10
     250 |            250 |              9
     500 |            500 |              9
    1000 |           1000 |              9
    1234 |           1000 |              9   (not found)

=== Binary search needs sorted input ===
array (unsorted): 9 3 7 1 8 2 5 4 6 0
binary_search for 8 => index -1  (value 8 IS present at index 4,
but binary search misses it because the input is not sorted).
```

Binary never exceeds ~⌈log₂ 1000⌉ = 10 probes; linear can hit 1000. The bottom
block is the catch: run binary search on unsorted data and it confidently returns
"not found" for a value that's right there.

## 3. Hash tables

[`03_hash_table.c`](03_hash_table.c) (`make run3`) is a string→int map using
**separate chaining**: a `djb2` string hash picks a bucket, and collisions live in
a linked list per bucket. Insert / lookup / delete are all here.

```
make run3
```
```
Insert 10 keys; note which bucket each lands in (collisions share one):
  put("apple     ",  1) -> bucket  7
  put("banana    ",  2) -> bucket  6
  ...
  entries=10 buckets=16 load=0.62  used buckets=10  longest chain=1

Lookups (average O(1) — at most one short chain to walk):
  get("cherry") = 3
  get("mango") = (not found)

Delete "banana", then look it up again:
  del("banana") = 1
  get("banana") = (not found)
```

The **longest chain = 1** line is the "is it really O(1)?" evidence: with a decent
hash and load factor < 1, buckets stay tiny, so a lookup walks ~1 node. Worst case
is still O(n) if every key collides — the hash's job is to make that not happen.

## 4. Trees & heaps

[`04_trees_heaps.c`](04_trees_heaps.c) (`make run4`) builds two structures. A
**binary search tree** keeps `left < node < right`, so an in-order walk emits keys
sorted. A **binary min-heap** (array-backed, parent ≤ children) gives a priority
queue with O(log n) push and pop-min.

```
make run4
```
```
=== Binary search tree ===
insert order: 50 30 70 20 40 60 80 35 65
in-order walk (always sorted): 20 30 35 40 50 60 65 70 80
contains(40)? yes   contains(99)? no

=== Binary min-heap (priority queue) ===
push: 5 1 8 3 9 2 7 4 6
pop-min repeatedly (comes out sorted ascending): 1 2 3 4 5 6 7 8 9
```

Repeated pop-min draining a heap is, in effect, **heapsort** — the elements come
out in order regardless of insertion order.

## 5. Graphs — BFS & DFS

[`05_graphs.c`](05_graphs.c) (`make run5`) stores an undirected graph as an
**adjacency list** (each vertex owns a list of neighbours) and traverses it two
ways. **BFS** uses a queue and visits nearest-first; **DFS** recurses, plunging
down one branch before backing up. Both are O(V + E).

```
make run5
```
```
BFS from 0: 0 2 1 5 4 3 6
DFS from 0: 0 2 5 6 4 1 3
```

BFS fans out level by level (0, then its neighbours, then theirs); DFS dives. The
exact neighbour order reflects how edges were inserted (front-insertion here).

## 6. Dynamic programming

[`06_dynamic_programming.c`](06_dynamic_programming.c) (`make run6`) shows DP's
whole value proposition by **counting function calls**. Naive recursive Fibonacci
recomputes the same subproblems exponentially often; memoization solves each once.

```
make run6
```
```
   n |    naive calls |     memo calls |       fib(n)
-----+----------------+----------------+-------------
  10 |            177 |             19 |           55
  20 |          21891 |             39 |         6765
  30 |        2692537 |             59 |       832040
  35 |       29860703 |             69 |      9227465
  40 |      331160281 |             79 |    102334155

=== DP part 2: 0/1 knapsack ===
items (weight,value): (1,1) (3,4) (4,5) (5,7)
capacity = 7
max value achievable = 9   (take items {3,4} : weight 3+4=7, value 4+5=9)
```

At n=40 the naive version makes **331 million** calls; memoization makes **79** —
same answer, ~4-million-fold less work. The knapsack table is a "real" DP: each
cell `dp[i][w]` is the best value using the first `i` items within budget `w`.

---

## 7. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`.

### Exercise 38.1 — Quicksort's partition  (`make ex1`)
Implement `partition` (Lomuto scheme) in
[`exercises/ex1_quicksort.c`](exercises/ex1_quicksort.c); the recursion is given.
Expected (`make sol1`):
```
before: 9 3 7 1 8 2 5 4 6 0 5 3
after:  0 1 2 3 3 4 5 5 6 7 8 9
sorted? YES
```

### Exercise 38.2 — A hash SET  (`make ex2`)
Implement `set_add` and `set_contains` in
[`exercises/ex2_hash_set.c`](exercises/ex2_hash_set.c) using chaining (keys only,
no values). Expected (`make sol2`):
```
adding: red(new) green(new) blue(new) red(dup) green(dup) yellow(new)
size = 4  (expected 4: red green blue yellow)
contains("blue") = 1
contains("purple") = 0
contains("red") = 1
```

### Exercise 38.3 — Edit distance (DP)  (`make ex3`)
Implement `edit_distance` (Levenshtein) in
[`exercises/ex3_edit_distance.c`](exercises/ex3_edit_distance.c). Expected
(`make sol3`):
```
edit("kitten", "sitting") = 3  (expected 3) OK
edit("flaw", "lawn") = 2  (expected 2) OK
edit("", "abc") = 3  (expected 3) OK
edit("same", "same") = 0  (expected 0) OK
edit("sunday", "saturday") = 3  (expected 3) OK
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **Asymptotic complexity** | O(n²) vs O(n log n) is the difference between a program that scales and one that doesn't — and you can *time* it |
| **Sorting (insertion / merge / quick)** | The canonical comparison-sort trade-offs; quicksort's pivot choice avoids its worst case |
| **Binary search** | O(log n) lookups — but only on sorted data; the invariant is the algorithm |
| **Hash tables** | Average O(1) insert/lookup/delete via a good hash + low load factor; chaining handles collisions |
| **BST & heap** | Ordered structure (in-order = sorted) vs priority queue (always-min at the root), both O(log n) when balanced |
| **Graphs, BFS/DFS** | Adjacency lists + two traversals are the substrate of shortest paths, dependency order, and computation graphs |
| **Dynamic programming** | Cache overlapping subproblems: exponential → polynomial, with the same answer |

## Further reading

- **CLRS — *Introduction to Algorithms* (Cormen, Leiserson, Rivest, Stein)**: the
  standard reference; every structure here gets a rigorous chapter:
  https://mitpress.mit.edu/9780262046305/introduction-to-algorithms/
- **MIT 6.1210 / 6.006 — *Introduction to Algorithms*** (lectures, problem sets,
  the course this module follows):
  https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/
- **VisuAlgo** — animated visualizations of sorting, hashing, BSTs, heaps, graphs,
  and DP; run them alongside the demos: https://visualgo.net/

**Next:** Module 39 — Advanced Algorithms — greedy and divide-and-conquer with
proofs, network flow, NP-completeness, and approximation (CLRS; MIT 6.1220/6.046).
*(Not yet built — see [the track plan](../cs-foundations-track.md).)* →
[../39_advanced_algorithms/README.md](../39_advanced_algorithms/README.md)
