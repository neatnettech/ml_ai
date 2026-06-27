# Module 44 — C++ for Systems

**Purpose:** This is the **optional capstone of the CS Foundations track**. You've
spent the whole track in C — pointers, manual `malloc`/`free`, hand-built data
structures — and that's exactly the right foundation. C++ is C plus **zero-cost
abstractions**: features that read at a high level but compile down to the same
machine code you'd have written by hand in C. The big three for systems work are
**RAII** (lifetimes tie cleanup to scope, so you can't leak), **templates**
(type-safe generics with no runtime cost), and the **STL** (the vector, hash map,
string, and sort you built by hand — battle-tested and free). This is the language of
**LLVM, Chromium/V8, game engines, high-frequency-trading systems, and most
performance-critical infrastructure**. Every demo here contrasts with the C you
already wrote.

**Prerequisites:** **Module 30 — C Programming I** (pointers, the stack/heap model,
`malloc`/`free`, and the hand-built vector/linked list we rewrite here) and ideally
**Module 38 — Data Structures** (so you recognize what the STL hands you for free).
Module 28 (bits & bytes) underlies all of it.

**What you'll learn:**
- **References vs pointers**, and **RAII**: a class that acquires a resource in its
  constructor and releases it in its destructor — deterministic cleanup at scope exit
  vs C's manual, forgettable `free`/`close`
- **Smart pointers** (`std::unique_ptr`, `std::shared_ptr`): how they replace manual
  `malloc`/`free`, the **move-only** semantics of `unique_ptr`, and why there's no
  leak path
- **Templates**: function and class templates (`max_of<T>`, `Stack<T>`) —
  compile-time polymorphism vs C's `void*`-based generics
- **The STL**: `std::vector`, `std::unordered_map`, `std::string`, iterators, and
  `<algorithm>` (`sort`, `find_if`) driven by **lambdas**
- **Rewriting Module 30's dynamic array** as idiomatic C++ — `std::vector<int>` and a
  hand-rolled RAII `Vec<T>` with the **rule of five**

> **Format:** this track is real source + a `Makefile` + this lab. This module is
> **C++ (`.cpp`)**, not C. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 44 runs **natively on Apple Silicon** (arm64) — no container needed. You need a
C++17 compiler; on macOS that's `clang++` from the Xcode Command Line Tools:

```bash
clang++ --version                     # Apple clang, ships with Xcode CLT
make run                              # build + run all five demos
```

Everything compiles with `clang++ -std=c++17 -Wall -Wextra -Wpedantic -g` and builds
the same on Linux (`g++`/`clang++`) or any C++17 host. Zero warnings on the whole
module.

---

## 1. References and RAII

C++ adds **references** — an alias for an existing object, like a pointer that can't
be null and needs no `*` to use — and **RAII** (*Resource Acquisition Is
Initialization*): tie a resource's lifetime to an object's. The constructor acquires
(open a file, allocate); the **destructor** releases — and the compiler runs the
destructor *automatically* at scope exit, on every path. [`01_references_raii.cpp`](01_references_raii.cpp)
wraps a `FILE*` in a `FileHandle` class (`make run1`):

```
=== References vs pointers ===
  after add_one_by_pointer(&x): x = 6
  after add_one_by_reference(x): x = 7
  alias = x; alias = 100; now x = 100 (same object)

=== RAII: deterministic cleanup at scope exit ===
  entering inner scope...
  [FileHandle] opened /tmp/m44_raii_demo.txt
  ...about to leave the inner scope
  [FileHandle] destructor fired -> closed the file
  back in main: the file is already closed.
```

The destructor fires the moment `fh` leaves the inner scope — no `fclose` anywhere in
sight. In C (Module 30) you `fopen` and must remember the matching `fclose` on *every*
return and error path; one missed branch leaks the handle. RAII makes that class of
bug impossible.

## 2. Smart pointers replace malloc/free

Module 30 drilled the rule "every `malloc` needs exactly one `free`." C++ encodes that
ownership in a **type**. `std::unique_ptr<T>` is the sole owner and frees on scope
exit (RAII for the heap); it's **move-only** so two owners can't double-free.
`std::shared_ptr<T>` shares ownership via a reference count, freeing when the last
owner dies. You never call `delete`. [`02_smart_pointers.cpp`](02_smart_pointers.cpp)
(`make run2`):

```
=== unique_ptr: sole owner, frees automatically ===
    Widget(1) constructed
  a owns Widget(1)
  leaving scope...
    Widget(1) destroyed
  (Widget(1) was freed at scope exit — no free() call needed)

=== unique_ptr is MOVE-ONLY: ownership transfers ===
    Widget(2) constructed
  after std::move: p is null (empty), q owns Widget(2)

=== shared_ptr: reference-counted shared ownership ===
    Widget(3) constructed
  s1 use_count = 1
  after copy, use_count = 2
  s2 leaving scope...
  after inner scope, use_count = 1 (object still alive)
```

Watch the destructors print exactly when each object dies. `std::move` *transfers*
ownership of the `unique_ptr` (the source becomes null); copying one wouldn't even
compile. The `shared_ptr`'s count rises to 2 when copied and falls back to 1 when the
copy dies — the object survives until the count hits 0.

## 3. Templates: compile-time generics

C's only generic mechanism is `void*` (think `qsort`): you erase the type, cast
everywhere, and the compiler can't check you. **Templates** let you write code once
and have the compiler stamp out a type-checked copy per concrete type — **compile-time
polymorphism** with no runtime cost. [`03_templates.cpp`](03_templates.cpp) has a
`max_of<T>` function template and a `Stack<T>` class template (`make run3`):

```
=== Function template: one max_of for every type ===
  max_of<int>(3, 9)        = 9
  max_of<double>(2.5, 1.5) = 2.5
  max_of('a', 'z') deduced = z

=== Class template: Stack<int> ===
  push(10), size=1
  push(20), size=2
  push(30), size=3
  pop -> 30
  pop -> 20
  pop -> 10

=== The SAME Stack template, now holding doubles ===
  pop -> 2.5
  pop -> 1.5
```

`Stack<int>` and `Stack<double>` are two distinct classes the compiler generated from
one template — both fully type-checked, no `void*`, no casts, no runtime dispatch. The
template argument can even be **deduced** from the call (`max_of('a','z')`).

## 4. The STL

In Modules 30 and 38 you hand-built a vector, a hash map, strings, and a sort. The
**Standard Template Library** ships all of them as tuned, tested templates:
`std::vector`, `std::unordered_map`, `std::string`, and `<algorithm>` (`sort`,
`find_if`) driven by **lambdas** (inline anonymous functions).
[`04_stl.cpp`](04_stl.cpp) (`make run4`):

```
=== std::vector<int>: growable array, no malloc/realloc ===
  size=6, contents: 1 4 9 16 25 36

=== <algorithm>: sort + find_if with a lambda ===
  sorted: 3 7 11 19 25 42
  first element > 15 is 19

=== std::string: real strings, no '\0' bookkeeping ===
  "hello, systems world" (length 20)

=== std::unordered_map: the Module 38 hash map, for free ===
  c    -> 3
  cpp  -> 2
  rust -> 1
```

`std::sort` is one line where C needs a `qsort` call with a comparator function and
casts; `find_if` takes a `[](int n){ return n > 15; }` lambda; `std::string` handles
the `'\0'`, growth, and concatenation you tracked by hand in Module 30; and
`unordered_map` is the Module 38 hash table with O(1)-average lookup. Every container
frees its own memory (RAII).

## 5. Rewriting Module 30's dynamic array in C++

Module 30's `05_dynamic_array.c` built a vector of ints from raw `malloc`/`realloc`/
`free`, a manual `{data, len, cap}` struct, hand-written bounds checks, and exactly
one `free` balancing all the growth. [`05_vector_cpp.cpp`](05_vector_cpp.cpp) rewrites
it two ways (`make run5`):

```
=== Part A: std::vector<int> (the C struct, done for you) ===
  size=10 cap=16  (capacity >= size; slack to grow)
  contents: 1 4 9 16 25 36 49 64 81 100
  at(20) is bounds-checked: threw std::out_of_range (C would read garbage)

=== Part B: a templated RAII Vec<T> (rule of five) ===
    (Vec grew capacity to 4)
    (Vec grew capacity to 8)
  size=5 cap=8 contents: 1 4 9 16 25
  after deep copy + push_back(999):
    original size=5 (unchanged), copy size=6
  after std::move: moved size=5, original size=0 (emptied)
```

**Part A** is the idiomatic answer: `std::vector<int>` *is* the C struct, grown and
freed for you, with the same 0→4→8→16 doubling and a bounds-checked `.at()`. **Part B**
hand-rolls a templated `Vec<T>` to show what `std::vector` does underneath — the
**rule of five** (destructor, copy ctor, copy assignment, move ctor, move assignment),
with the destructor owning the single `delete[]` and copy/move written explicitly.

### C vs C++ for the same task

| Concern | C (Module 30, `05_dynamic_array.c`) | C++ (this module) |
|---------|-------------------------------------|-------------------|
| Allocation | manual `realloc`, captured in a temp to avoid leak-on-fail | `std::vector` / `new[]` inside `grow()` |
| Freeing | one hand-written `vec_free` you must remember to call | destructor runs automatically at scope exit |
| Bounds safety | none — `v.data[i]` reads garbage out of range | `.at()` throws `std::out_of_range` |
| Generic over types | not generic — it's `int`-only (you'd copy-paste or use `void*`) | `std::vector<T>` / templated `Vec<T>` |
| Copy / move | you write it by hand and risk aliasing the same buffer | copy = deep copy, move = steal; both leak-free |

Same algorithm, same `0→4→8→16` growth — but the compiler now owns the cleanup and the
type system owns the safety.

---

## 6. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`.

### Exercise 44.1 — An RAII buffer wrapper  (`make ex1`)
Implement the constructor and destructor of `Buffer` in
[`exercises/ex1_raii_buffer.cpp`](exercises/ex1_raii_buffer.cpp) so it `new[]`s its
ints on construction and `delete[]`s them on destruction — proving the cleanup runs at
scope exit. Expected (`make sol1`):
```
=== RAII buffer ===
  [Buffer] allocated 4 ints
  contents: 0 10 20 30
  leaving scope (destructor should fire next)...
  [Buffer] freed 4 ints
  back in main: buffer already freed.
```

### Exercise 44.2 — A generic `clamp` template  (`make ex2`)
Implement `template <typename T> T clamp(T v, T lo, T hi)` in
[`exercises/ex2_clamp.cpp`](exercises/ex2_clamp.cpp) and use it with both `int` and
`double` from the one definition. Expected (`make sol2`):
```
=== clamp<int> ===
  clamp(5, 0, 10)   = 5
  clamp(-3, 0, 10)  = 0
  clamp(99, 0, 10)  = 10
=== clamp<double> (same template) ===
  clamp(0.5, 0.0, 1.0)  = 0.5
  clamp(2.5, 0.0, 1.0)  = 1.0
```

### Exercise 44.3 — Rewrite a C-style loop with the STL  (`make ex3`)
Replace a hand-written bubble sort + manual count (shown in the file) with
`std::vector`, `std::sort`, `std::count_if` and a lambda in
[`exercises/ex3_stl_rewrite.cpp`](exercises/ex3_stl_rewrite.cpp) — same result, far
less code. Expected (`make sol3`):
```
=== STL rewrite ===
  sorted: 3 7 11 19 25 42
  count > 20 = 2
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **References vs pointers** | A reference is a can't-be-null alias — cleaner pass-by-reference than C's `&`/`*` |
| **RAII** | Constructor acquires, destructor releases at scope exit — cleanup you can't forget, on every path |
| **Smart pointers** | `unique_ptr`/`shared_ptr` replace `malloc`/`free`; move-only ownership and ref-counting remove the leak path |
| **Templates** | Type-safe, zero-cost generics — compile-time polymorphism that replaces C's `void*` and casts |
| **The STL** | `vector`, `unordered_map`, `string`, `sort`, `find_if` — Modules 30/38 handed to you, tuned and tested |
| **Rule of five** | When a type owns a resource, define dtor + copy/move so ownership is correct and leak-free |

## Further reading

- **Bjarne Stroustrup — *A Tour of C++* (3rd ed.)**: the fastest accurate overview of
  modern C++ from the language's creator; pairs directly with this module.
- **cppreference** — the reference for the standard library and language, with runnable
  examples: https://en.cppreference.com/
- **Scott Meyers — *Effective Modern C++*** (42 items on C++11/14): smart pointers,
  move semantics, and `auto` done right — the natural deepening after this module.

**Next:** this is the **end of the CS Foundations track** — you've gone from a single
bit (Module 28) through assembly, the CPU, memory, the OS, and security, and capped it
with the systems language layered on top of C. Where to go next is up to you; see
[the track plan](../cs-foundations-track.md) for the full map and the phase-by-phase
list of what you've covered. You've completed the track.
