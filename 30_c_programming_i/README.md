# Module 30 — C Programming I

**Purpose:** This is where you truly meet **pointers and the memory model** — the
reason C sits at the center of this track. A pointer is just a variable holding a
memory address, and once you can *see* addresses, take them with `&`, follow them
with `*`, and tell the **stack** from the **heap**, the rest of systems programming
opens up. The deliverable is a working set of memory demos plus **a dynamic array
(vector) and a linked list you build from raw `malloc`/`free` and pointers** — the
two data structures every later module (assembly, virtual memory, the kernel)
assumes you can reason about byte by byte.

**Prerequisites:** Module 28 (Bits & Bytes) — you should be comfortable that every
value is a fixed run of bytes at some address. Module 29 (Digital Logic & the CPU)
is helpful for intuition about what "memory" physically is, but not required.

> **New to C entirely?** Start with [Module 47 — C & C++ From Zero](../47_c_cpp_from_zero/)
> for a gentle, self-contained intro to the language, then come back here for the
> bytes-up version that ties pointers to the hardware memory model.

**What you'll learn:**
- **Pointers**: addresses, `&` and `*`, pointer arithmetic, and how an array name
  *decays* to a pointer — so `a[i]` is literally `*(a + i)`
- **Pass-by-value vs pass-by-pointer**: why `swap` needs addresses, and how C does
  "output parameters"
- **Stack vs heap**: automatic locals (freed at return) vs `malloc`'d memory (yours
  to `free`), the classic **dangling-pointer** bug, and why the stack grows *down*
- **C strings**: NUL-terminated char arrays, the off-by-one for `'\0'`, and
  `strlen`/`strcpy`/`strcmp` reimplemented from scratch
- **structs**: by value vs by pointer, the `->` operator, arrays of structs, and
  `sizeof` / alignment **padding**
- The capstone: a heap-backed **vector** that grows via `realloc`, and a **linked
  list** — pointers + heap made concrete, with **every `malloc` balanced by a `free`**

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 30 runs **natively on Apple Silicon** (arm64) — no container needed. You only
need `clang` + `make` (Xcode Command Line Tools):

```bash
make run                              # build + run all five demos
```

Everything is portable C11 (`-std=c11 -Wall -Wextra -Wpedantic -g`), so it also
builds on Linux or inside the x86-64 `setup/` container from Module 28. The code is
**memory-correct** — every `malloc` has a matching `free`, no leaks on the happy
path — because Module 31 introduces `valgrind` and you'll re-run these clean.

> **Addresses vary every run.** All the demos print real memory addresses. The exact
> hex values below are from one run on this machine; **yours will differ** (and
> change run to run, thanks to address-space layout randomization). What matters is
> the *relationships* — equal addresses, decreasing addresses, the byte gaps.

---

## 1. Pointers: `&`, `*`, decay, and pass-by-pointer

A **pointer** holds the address of an object. `&x` gives you x's address; `*p`
*dereferences* — follows the address back to the object. An array name **decays** to
a pointer to its first element, so indexing is pointer arithmetic in disguise.
[`01_pointers.c`](01_pointers.c) (`make run1`):

```
=== Variables have addresses ===
  x = 42  lives at address &x = 0x16b0d2388
  y = 7  lives at address &y = 0x16b0d2384

=== A pointer holds an address; * follows it ===
  p   = 0x16b0d2388   (the value stored IN p is x's address)
  *p  = 42    (dereference: the int p points at)
  after *p = 100, x is now 100  (we changed x via p)

=== Pass by value vs pass by pointer ===
  add_one_by_value(x): x is still 5 (copy was changed, not x)
  add_one_by_pointer(&x): x is now 6 (changed through the address)

=== swap really swaps ===
  before: x = 6, y = 7
  after : x = 7, y = 6

=== Arrays decay to pointers; pointer arithmetic ===
  a       = 0x16b0d2390   (array name decays to &a[0])
  &a[0]   = 0x16b0d2390   (same address)
  a[2] = 30, *(a + 2) = 30  (identical: indexing IS pointer math)
  walking with a pointer: 10 20 30 40 50
  (q+1) - q = 1 element, = 4 bytes apart in memory
```

Two takeaways: `swap` is impossible by value (you'd swap copies) and trivial by
pointer; and pointer arithmetic counts in **elements**, not bytes — `q + 1` advances
by `sizeof(int)` bytes.

## 2. Stack vs heap, and the dangling-pointer bug

C gives you two storage regions you manage yourself. **Stack** locals are automatic:
freed the instant their function returns. **Heap** memory from `malloc` lives until
*you* `free` it. The #1 beginner bug is returning a pointer to a stack local — it
dangles immediately. [`02_stack_heap.c`](02_stack_heap.c) (`make run2`) shows this
**without** ever dereferencing the dead pointer:

```
=== Stack frames stack downward (addresses decrease) ===
  main:   a local lives at 0x16f99e380
  level1: a local lives at 0x16f99e32c
   level2: a local lives at 0x16f99e30c
    level3: a local lives at 0x16f99e2ec
  (each deeper call's local sits at a LOWER address — the stack grows down)

=== The dangling-pointer bug (shown safely) ===
  call 1: local n=1 lives at 0x16f99e328 (this slot is reused after return)
  call 2: local n=2 lives at 0x16f99e328 (this slot is reused after return)
  ^ same address twice => that storage is transient. Returning &n from
    such a function gives the caller a DANGLING pointer; dereferencing it
    is Undefined Behavior. The fix is the heap, below.

=== The heap fix: malloc / free ===
  correct_make_int: heap int=99 lives at 0x100b6e1e0 (caller will free it)
  *heap = 99  (safe: real, owned memory)
  freed it. (Set heap = NULL after free to avoid use-after-free.)

=== A heap array vs a stack array ===
  stack array at 0x16f99e388 (auto-freed at return)
  heap array  at 0x100b6e1e0, contents: 0 1 4 9
```

Notice the stack addresses (`0x16f9...`) march *downward* with each nested call,
while the heap address (`0x100b...`) is in a completely different region. The same
stack slot is reused across two calls — proof that any pointer into it would dangle.
The fix is `malloc`; the caller owns the memory and `free`s it exactly once.

## 3. C strings are NUL-terminated char arrays

C has no string type — a "string" is a `char` array ending in a `'\0'` (value 0).
Every standard string function depends on that terminator, and the constant gotcha
is the **off-by-one**: storing an N-char string needs N+1 bytes.
[`03_strings.c`](03_strings.c) (`make run3`) reimplements the big three with
pointers:

```
=== A string is chars + a '\0' terminator ===
  "hi" occupies sizeof = 3 bytes (2 chars + 1 NUL)
  bytes (char=value): h=104 i=105 \0=0
  (the trailing byte is value 0 — that's the terminator)

=== my_strlen vs the off-by-one ===
  my_strlen("pointers") = 8  (chars before '\0')
  bytes needed to STORE it = 9  (length + 1 for the '\0')

=== my_strcpy into a stack buffer, sized safely ===
  copied "hello, C" -> buf, which now reads "hello, C"

=== my_strcmp ===
  my_strcmp("abc", "abc") = 0  (equal)
  my_strcmp("abc", "abd") = -1  (negative: 'c' < 'd')
  my_strcmp("abz", "abc") = 23  (positive: 'z' > 'c')
  my_strcmp("ab",  "abc") = -99  (negative: shorter sorts first)
```

`my_strlen` walks until the NUL and returns the pointer difference; `my_strcpy`
copies *including* the `'\0'`; `my_strcmp` returns the signed difference of the first
mismatching bytes. The copy is guarded against overflowing the fixed stack buffer —
the safety habit that the entire memory-safety half of this track is about.

## 4. structs: value vs pointer, `->`, and padding

A `struct` groups fields into one object. Pass it **by value** (a full copy) or **by
pointer** (cheap, and you can mutate the original); `ptr->field` is just sugar for
`(*ptr).field`. The compiler inserts **padding** so each field is aligned, so
`sizeof` can exceed the raw field-byte total. [`04_structs.c`](04_structs.c)
(`make run4`):

```
=== pass by value vs by pointer ===
  a after move_by_value = (3, 4)
  a after move_by_pointer = (103, 104)

=== the -> operator ===
  pp->x = 10, (*pp).x = 10  (identical syntaxes)

=== nested struct + an array of structs ===
  crew[0]: Ada    age 36, home (1,2)
  crew[1]: Grace  age 44, home (3,4)

=== sizeof, padding, and alignment ===
  sizeof(struct Point)  = 8  (two ints, tightly packed)
  sum of field sizes    = 28 bytes
  sizeof(struct Person) = 28  (>= the sum; here the fields already align)
  struct{char;int;char} = 12 bytes (padded for the int's alignment)
```

`move_by_value` leaves the original untouched (it mutated a copy); `move_by_pointer`
changes it through the address. The padding payoff is the last line: `char; int;
char` has 6 bytes of fields but `sizeof` is **12**, because the `int` must land on a
4-byte boundary and the struct's size is rounded up to its alignment. Field order
affects layout — a lesson Module 33 (caches) revisits.

## 5. Capstone: a dynamic array (vector) that grows

This ties it all together: a struct that **owns** a heap buffer, growing via
`realloc` (double the capacity when full — amortized O(1) push). `vec_new` /
`vec_push` / `vec_get` / `vec_free`, with one `free` balancing all the growth.
[`05_dynamic_array.c`](05_dynamic_array.c) (`make run5`):

```
=== Build a vector by pushing; watch it grow ===
  empty vector: len=0 cap=0 data=0x0
  push(1):
    (grew capacity to 4)
  push(4):
  push(9):
  push(16):
  push(25):
    (grew capacity to 8)
  push(36):
  push(49):
  push(64):
  push(81):
    (grew capacity to 16)
  push(100):

=== Read it back ===
  len=10 cap=16  (cap >= len; the slack is room to grow)
  contents: 1 4 9 16 25 36 49 64 81 100

  freed. data=0x0, len=0 (safe to reuse or discard)
```

Capacity jumps 0 → 4 → 8 → 16: it only `realloc`s when full, so most pushes are a
single store. `realloc`'s result is captured in a temporary first — assigning it
straight back to `data` would leak the old block if the allocation failed. This is
exactly how `std::vector`, Python `list`, and Go slices work underneath.

---

## 6. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`.

### Exercise 30.1 — Reverse a string in place  (`make ex1`)
Implement `my_strrev` in [`exercises/ex1_strrev.c`](exercises/ex1_strrev.c) using two
pointers that walk toward each other — no extra buffer. Expected (`make sol1`):
```
reversed: "sretniop"
reversed: "C"
reversed: "" (empty stays empty)
```

### Exercise 30.2 — A singly linked list  (`make ex2`)
Implement `push_front`, `length`, and `free_list` in
[`exercises/ex2_linked_list.c`](exercises/ex2_linked_list.c) — structs, `malloc`, and
pointer chasing. Remember to save `next` *before* you `free` a node. Expected
(`make sol2`):
```
  list: 1 -> 2 -> 3 -> NULL
  length = 3
  freed.
```

### Exercise 30.3 — Extend the vector: `vec_pop` and `vec_sum`  (`make ex3`)
Implement `vec_pop` (remove and return the last element) and `vec_sum` in
[`exercises/ex3_vec_ops.c`](exercises/ex3_vec_ops.c), building on the demo's vector.
Expected (`make sol3`):
```
sum of [1..5] = 15
pop -> 5
pop -> 4
len after two pops = 3
sum now = 6
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **Pointers (`&`, `*`)** | A pointer is an address; `&` takes one, `*` follows it — the basis of every C data structure |
| **Array/pointer decay & arithmetic** | `a[i]` *is* `*(a+i)`; pointer math counts in elements — how you iterate and slice memory |
| **Pass by value vs pointer** | Copies don't escape; pointers give mutation and output params — why `swap` needs addresses |
| **Stack vs heap & dangling pointers** | Locals die at return; heap lives until `free` — the source of dangling-pointer and leak bugs |
| **C strings & the `'\0'`** | Strings are NUL-terminated arrays; the off-by-one and buffer sizing are where memory bugs start |
| **structs, `->`, alignment** | Group data, pass cheaply by pointer; padding makes `sizeof` exceed the field sum |
| **Vector & linked list from `malloc`** | `realloc`-growth and pointer-chained nodes — the concrete payoff, leak-free |

## Further reading

- **K&R — Brian Kernighan & Dennis Ritchie, *The C Programming Language* (2nd ed.)**:
  the canonical, terse C book; Chapter 5 (Pointers and Arrays) pairs with this module.
- **CS:APP3e, Chapter 3 intro — Machine-Level Representation of Programs** (the
  memory/stack model this module builds intuition for): http://csapp.cs.cmu.edu/
- **Beej's Guide to C Programming** (free, modern, friendly — great for pointers,
  strings, and structs): https://beej.us/guide/bgc/

**Next:** Module 31 — C Programming II — multi-file builds, Makefiles, `gdb`/`valgrind`
(leak-check these very labs!), function pointers, the preprocessor, and Undefined
Behavior. See [../31_c_programming_ii/README.md](../31_c_programming_ii/README.md).
*(Not yet built — see [the track plan](../cs-foundations-track.md).)*
