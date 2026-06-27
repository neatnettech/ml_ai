# Module 31 — C Programming II

**Purpose:** Module 30 taught the C *language* — pointers, the stack/heap, `malloc`/
`free`. This module teaches how to *build real C programs* with it: splitting code
across files and letting the **linker** join them, driving the **toolchain** with a
`Makefile`, using **function pointers** for callbacks and dispatch tables, wielding
(and surviving) the **preprocessor**, understanding **undefined behavior** — the
bargain that makes C fast and dangerous — and using **debuggers and memory checkers**
to find the bugs UB lets through. These are the day-to-day mechanics every later
systems module (assembly, linking/loading, the kernel) assumes you already have.

**Prerequisites:** Module 30 (C pointers, the memory model, `malloc`/`free`). Module
28 helps but isn't required.

**What you'll learn:**
- **Multi-file builds**: `.h` declarations vs `.c` definitions, translation units,
  separate compilation, and what the **linker** actually does
- **Function pointers**: storing functions in variables, **dispatch tables**, and
  passing **callbacks/comparators** (including `qsort` from the standard library)
- **The preprocessor**: `#define` constants and function-like macros, their classic
  pitfalls (missing parens, double evaluation), `#ifdef` conditional compilation,
  `assert` — and why a `static inline` function is the safer choice
- **Undefined behavior**: signed overflow, out-of-bounds access, use-after-free,
  uninitialized reads — what they are, why they're dangerous, and the defined fix
- **Debugging**: the `lldb`/`gdb` and `valgrind` workflow for crashes and leaks

> **Format:** real C, not notebooks. Source files + a `Makefile` + this lab. Build
> with `make`, run a demo with `make run1`, attempt an exercise in `exercises/`,
> check against `solutions/`.

## Setup

Everything that **builds and runs** in this module is **native on Apple Silicon** —
just `clang` + `make` (Xcode Command Line Tools):

```bash
make run          # build + run all five demos
make run3-debug   # demo 3 rebuilt with -DDEBUG (conditional compilation)
```

The **debugger** section uses **`lldb`**, the native macOS debugger (ships with the
Command Line Tools). **`valgrind` is Linux-only** and is *not* available on arm64
macOS — so no `make` target depends on it. To run the `valgrind`/`gdb` workflow in
§5, use the **x86-64 Linux container** from Module 28's
[`setup/README.md`](../28_bits_and_bytes/setup/README.md); the commands and
expected-style output are given below so you can follow along either way.

---

## 1. Multi-file programs: headers, translation units, linking

A real program is many `.c` files. The mechanism that lets them call each other is
the split between **declarations** (in `.h` headers) and **definitions** (in `.c`
files), joined by the **linker**.

- A **header** ([`mathlib.h`](mathlib.h)) contains *declarations* — `int gcd(int, int);`
  — promises that "a function named `gcd` with this signature exists somewhere." A
  caller `#include`s the header so the compiler knows the name and types.
- A **`.c` file** ([`mathlib.c`](mathlib.c)) contains the *definitions* — the actual
  code. Each `.c` file is a **translation unit**, compiled independently into an
  **object file** (`.o`) of machine code plus a table of symbols.
- The **linker** takes the object files and resolves each *call* to `gcd` in one
  unit against the *definition* of `gcd` in another. If no `.o` defines a symbol you
  called, you get the famous *"undefined reference"* / *"Undefined symbols"* error.

[`01_multifile_main.c`](01_multifile_main.c) includes the header and calls the
library. The `Makefile` does the two-step build explicitly:

```
clang -c mathlib.c           -> bin/mathlib.o            (defines the symbols)
clang -c 01_multifile_main.c -> bin/01_multifile_main.o  (calls them; unresolved)
clang bin/mathlib.o bin/01_multifile_main.o -o bin/01_multifile   (linker joins)
```

The header's **include guard** (`#ifndef MATHLIB_H … #endif`) ensures the
declarations expand only once even if the header is included many times.

```
make run1
```
```
── demo 1: multi-file ──
=== gcd ===
  gcd(48, 36)  = 12
  gcd(17, 5)   = 1
  gcd(-12, 8)  = 4

=== ipow ===
  ipow(2, 10)  = 1024
  ipow(3, 4)   = 81
  ipow(5, 0)   = 1

=== is_prime ===
  primes < 30: 2 3 5 7 11 13 17 19 23 29
```

## 2. Function pointers

A function name decays to the **address of its code**, so you can keep a function in
a variable, in a table, or pass it as a parameter. This is how C does polymorphism:
one generic routine, behavior supplied by the caller.
[`02_function_pointers.c`](02_function_pointers.c) shows three uses plus the
standard library's own:

- A **dispatch table** — `struct {const char *name; int (*fn)(int,int);}[]` — looks
  up behavior by string (the pattern behind command interpreters and opcode tables).
- A **callback**: `map(arr, n, f)` applies a caller-supplied `int (*f)(int)` to every
  element; `map` itself knows nothing about the work.
- **`qsort`** from `<stdlib.h>` is fully generic over byte arrays — *you* supply the
  comparator `int cmp(const void*, const void*)`. Swapping the two arguments inside
  the comparator flips ascending into descending.

```
make run2
```
```
── demo 2: function pointers ──
=== dispatch table (lookup behavior by name) ===
  add(6, 4) = 10
  mul(6, 4) = 24
  sub(6, 4) = 2
  div: unknown op

=== map: apply a callback to every element ===
  start:   1 2 3 4 5
  square:  1 4 9 16 25
  negate:  -1 -4 -9 -16 -25

=== qsort with a custom comparator ===
  unsorted:    5 2 9 1 7 3
  ascending:   1 2 3 5 7 9
  descending:  9 7 5 3 2 1
```

> Read the declaration `int (*fn)(int, int)` inside-out: "`fn` is a pointer to a
> function taking `(int, int)` and returning `int`." The parentheses around `*fn`
> are required — without them `int *fn(int,int)` is a function returning `int *`.

## 3. The preprocessor (and why it bites)

Before the compiler proper runs, the **preprocessor** does pure *text substitution*:
`#include`, `#define` replacement, `#if`/`#ifdef`. It does **not** understand C — it
just moves tokens — which is the source of every classic macro bug.
[`03_preprocessor.c`](03_preprocessor.c) demonstrates:

- **Object-like macros** for named constants (`#define MAX_USERS 100`).
- **Pitfall A — missing parentheses.** `#define SQUARE_BAD(x) x*x` expands
  `SQUARE_BAD(2 + 3)` to `2 + 3 * 2 + 3 = 11`, not 25. Fix: parenthesize the whole
  expansion *and* every parameter — `#define SQUARE_OK(x) ((x)*(x))`.
- **Pitfall B — double evaluation.** `#define MAX(a,b) ((a)>(b)?(a):(b))` pastes the
  argument text twice, so `MAX(a++, b)` increments `a` *twice*.
- **The safe alternative:** a `static inline int max_int(int,int)` evaluates each
  argument exactly once, is type-checked, and inlines to the same speed as the macro.
- **`#ifdef`** for conditional compilation, and **`assert`** for checked invariants
  (compiled out with `-DNDEBUG`).

```
make run3
```
```
── demo 3: preprocessor ──
=== object-like macros ===
  GREETING  = hello from the preprocessor
  MAX_USERS = 100

=== pitfall A: SQUARE without parentheses ===
  SQUARE_BAD(2 + 3) expands to 2 + 3 * 2 + 3 = 11  (WRONG)
  SQUARE_OK(2 + 3)  = 25  (correct)

=== pitfall B: MAX double-evaluates its arguments ===
  after MAX(a++, b): result=6, a=7  (a jumped by 2, surprise!)
  after max_int(x++, y): result=5, x=6  (a clean single increment)

=== conditional compilation (#ifdef) ===
  release build: define DEBUG (make run3-debug) for extra output

=== assert: a checked invariant (compiled out with -DNDEBUG) ===
  assert(users <= MAX_USERS) passed (users=42)
```

`make run3-debug` rebuilds with `-DDEBUG` so the `#ifdef DEBUG` branch lights up:

```
=== conditional compilation (#ifdef) ===
  DEBUG build: verbose diagnostics enabled
```

> See the raw post-preprocessor text yourself: `clang -E 03_preprocessor.c | less`.

## 4. Undefined behavior

The C standard leaves many situations **undefined**: the compiler may do *anything*
— return garbage, crash, or silently "work" today and miscompile tomorrow. UB is the
bargain that makes C fast: the compiler **assumes you never trigger it** and
optimizes on that assumption (e.g. that `x + 1 > x` is always true, which is only
valid if signed overflow can't happen). [`04_undefined_behavior.c`](04_undefined_behavior.c)
does **not** execute any UB — for each trap it explains the hazard and shows the
**defined** alternative:

| UB | Why it's a trap | The defined fix |
|----|-----------------|-----------------|
| **Signed overflow** | `INT_MAX + 1` is UB, not "wraps to `INT_MIN`" | compute in **`unsigned`** (modular), or check `a > INT_MAX - b` *before* adding |
| **Out-of-bounds access** | no bounds checking exists in C; reads junk or corrupts neighbors | carry the length, check `idx < len` yourself |
| **Use-after-free** | a freed pointer still holds an address; dereferencing it is UB | set the pointer to `NULL` right after `free`, guard before use |
| **Uninitialized read** | a stack variable starts with indeterminate bits | always initialize at declaration |

```
make run4
```
```
── demo 4: undefined behavior ──
=== 1. Signed integer overflow ===
  INT_MAX            = 2147483647
  (signed) INT_MAX+1 = UNDEFINED BEHAVIOR (do not rely on it)
  unsigned INT_MAX+1 = 2147483648  (defined: wraps mod 2^32)
  a + b would overflow -> refused (checked a > INT_MAX - b)

=== 2. Out-of-bounds array access ===
  arr[7]: out of bounds (len=5) -> refused, not read
  in-bounds arr[4] = 50  (the checked, defined access)

=== 3. Use-after-free / dangling pointer ===
  before free: p = "live data"
  after free + p=NULL: dereferencing p would be UB; p is now NULL
  guarded: we check p != NULL before any use

=== 4. Reading an uninitialized variable ===
  uninitialized int: reading it is UB (could be any bit pattern)
  initialized int = 0  (always assign before you read)

Takeaway: UB is the compiler's license to optimize hard — it ASSUMES
you never do these. Tools (demo 5) catch the cases discipline misses.
```

> **Sanitizers** are the modern way to catch UB at runtime. Rebuild any demo with
> `-fsanitize=address,undefined` and the program will print a precise report the
> moment it hits an overflow, bad index, or use-after-free. AddressSanitizer (ASan)
> and UndefinedBehaviorSanitizer (UBSan) are built into `clang` and work natively on
> macOS — they're the everyday complement to `valgrind`.

## 5. Debugging: lldb / gdb and valgrind

[`05_debugging.c`](05_debugging.c) ships **working** (no crash on a default build).
Its `sum_array` once had a classic off-by-one — `i <= n` instead of `i < n`, walking
one element past the array (an out-of-bounds read, §4). This section walks the
workflow you'd use to find such a bug. The `-g` flag (already in `CFLAGS`) embeds
source-line info so the debugger can show your code.

```
make run5
```
```
── demo 5: debugging ──
=== sum_array ===
  sum of 8 elements = 31  (expected 31)

=== make_range + free ===
  range: 1 2 3 4 5

To practice: see README §5 for the lldb session and the valgrind run
(valgrind lives in the x86-64 container; lldb is native on macOS).
```

### lldb (native on macOS)

`lldb` is the LLVM debugger that ships with Xcode's Command Line Tools. Set a
breakpoint, run, inspect locals, step. This is a **real captured session** on this
arm64 Mac:

```
$ lldb ./bin/05_debugging
(lldb) breakpoint set --name sum_array
Breakpoint 1: where = 05_debugging`sum_array + 12 at 05_debugging.c:21:10
(lldb) run
Process launched
* thread #1, stop reason = breakpoint 1.1
    frame #0: 05_debugging`sum_array(a=0x000000016fdfe210, n=8) at 05_debugging.c:21:10
   21      long total = 0;
(lldb) frame variable a n
(const int *) a = 0x000000016fdfe210
(int) n = 8
(lldb) next                    # step over, line by line
(lldb) print total             # inspect a value
(lldb) continue                # resume
(lldb) quit
```

The everyday `lldb` commands: `breakpoint set --name F` (or `b F`), `run` (`r`),
`next` (`n`, step over), `step` (`s`, step into), `print EXPR` (`p`), `frame variable`
(all locals), `bt` (backtrace), `continue` (`c`), `quit` (`q`). To catch the original
off-by-one you'd break on `sum_array`, then `watch i` (or step the loop) and see `i`
reach `n` and index off the end.

### gdb (via the container — same commands)

`gdb` uses near-identical commands and is the CS:APP-standard debugger. Run it in the
x86-64 Linux box from Module 28's `setup/` (gdb on macOS needs codesigning and isn't
set up here):

```
$ gdb ./bin/05_debugging
(gdb) break sum_array
(gdb) run
(gdb) info locals
(gdb) next
(gdb) print total
(gdb) continue
```

### valgrind (Linux-only — run in the x86-64 container)

`valgrind` runs your binary on a synthetic CPU and reports **every** invalid memory
access and leak with a stack trace — it catches bugs that *happen* to not crash. It
is **Linux-only and not available on arm64 macOS**, so nothing in this `Makefile`
depends on it; run it inside the Module 28 container.

A clean run of `05_debugging` reports no errors:

```
$ valgrind --leak-check=full ./bin/05_debugging
==1234== Memcheck, a memory error detector
...
==1234== All heap blocks were freed -- no leaks are possible
==1234== ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)
```

If you reintroduce the off-by-one (`i <= n`), valgrind pinpoints the bad read:

```
==1234== Invalid read of size 4
==1234==    at 0x...: sum_array (05_debugging.c:23)
==1234==  Address 0x... is 0 bytes after a block of size 32 alloc'd
```

And if you delete the `free(r)` in `make_range`, it reports the leak:

```
==1234== 20 bytes in 1 blocks are definitely lost in loss record 1 of 1
==1234==    at 0x...: malloc
==1234==    by 0x...: make_range (05_debugging.c:39)
```

*(Output above is the standard valgrind format, shown for reference — it was not run
on this Mac. ASan from §4 gives equivalent reports natively.)*

---

## 6. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`.

### Exercise 31.1 — Add `lcm` to the library  (`make ex1`)
The multi-file edit loop in miniature: declare `int lcm(int,int);` in
[`mathlib.h`](mathlib.h), define it in [`mathlib.c`](mathlib.c) using the existing
`gcd` (`lcm = |a/gcd(a,b)*b|`, divide first to limit overflow), then call it from
[`exercises/ex1_lcm.c`](exercises/ex1_lcm.c). Expected (`make sol1`):
```
lcm(4, 6)   = 12  (expected 12)
lcm(21, 6)  = 42  (expected 42)
lcm(5, 0)   = 0  (expected 0)
lcm(12, 18) = 36  (expected 36)
```

### Exercise 31.2 — Generic `find` with a predicate  (`make ex2`)
Implement `int find(int *arr, int n, int (*pred)(int))` returning the index of the
first matching element (or -1) in [`exercises/ex2_find.c`](exercises/ex2_find.c).
The same routine works for any rule. Expected (`make sol2`):
```
first even     at index 2  (expected 2)
first negative at index 3  (expected 3)
first even in {1,3,5} = -1  (expected -1)
```

### Exercise 31.3 — A correct `MIN` macro and its safe twin  (`make ex3`)
In [`exercises/ex3_min_macro.c`](exercises/ex3_min_macro.c) write `MIN(a,b)` with
full parenthesization, and `static inline int min_int(int,int)`. The main feeds
`a++` to both so you *see* the macro double-evaluate. Expected (`make sol3`):
```
MIN(3, 7)     = 3  (expected 3)
min_int(3, 7) = 3  (expected 3)

MIN(a++, 100) = 6, a = 7   <- macro bumped a TWICE
min_int(b++,100) = 5, b = 6  <- function bumped b ONCE
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **Headers vs definitions, the linker** | `.h` declares, `.c` defines; the linker resolves calls across translation units — the basis of every multi-file project and library |
| **Separate compilation** | each `.c` becomes a `.o` independently, so a one-file change rebuilds and relinks fast; Makefiles automate the dependency graph |
| **Function pointers** | callbacks, dispatch tables, and `qsort` comparators — C's mechanism for "behavior as a parameter" |
| **The preprocessor** | text substitution before compilation; powerful but precedence-blind — parenthesize macros, beware double evaluation, prefer `static inline` |
| **Undefined behavior** | the assumption that makes C fast and unsafe; know the classic traps and their defined fixes |
| **Debuggers & memory checkers** | `lldb`/`gdb` to step and inspect, `valgrind`/sanitizers to catch invalid memory and leaks — how you find the bugs UB lets through |

## Further reading

- **The C Programming Language (K&R), 2nd ed.** — the canonical C text; chapters 4–6
  cover functions/scope, the preprocessor, and pointers in depth.
- **CS:APP3e, Chapter 7 — Linking** (the authoritative treatment of object files,
  symbol resolution, and static/dynamic libraries): http://csapp.cs.cmu.edu/
- **"A Guide to Undefined Behavior in C and C++" (John Regehr)** — why UB exists and
  how compilers exploit it: https://blog.regehr.org/archives/213
- **Beej's Guide to C Programming** — a friendly, modern, free full-language guide:
  https://beej.us/guide/bgc/

**Next:** Module 32 — Assembly & the ISA — read `gcc -S`/`objdump`, learn registers,
the calling convention, and stack frames, then defuse a binary bomb (CS:APP ch.3 +
Bomb/Attack Lab). *(Not yet built — see [the track plan](../cs-foundations-track.md);
the lab will live at ../32_assembly/README.md.)*
