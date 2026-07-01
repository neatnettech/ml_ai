# Module 47 — C & C++ From Zero

**Purpose:** A **standalone, beginner-friendly on-ramp** to the C and C++
*languages* — for someone who has never compiled a program and just wants to learn
C, then C++. You start at "hello world + how does compiling work," walk through the
core of C (types, control flow, functions, arrays, pointers, structs, `malloc`/
`free`), then meet the C++ tools that make the same ideas shorter and safer
(`iostream`, references, `std::string`/`std::vector`, a class with RAII, a taste of
templates). Every demo is real source you build with `make` and run.

> **This module overlaps [Module 30](../30_c_programming_i/) and
> [Module 44](../44_cpp_for_systems/) on purpose — the difference is the audience.**
> M30/M44 are the CS-Foundations *systems* track: they assume the bytes-up modules
> before them ([Module 28](../28_bits_and_bytes/) onward) and frame C/C++ as "the
> machine, up close." **M47 assumes nothing.** It teaches pointers *operationally*
> ("a variable that holds an address"), not from the CPU up. When you finish here,
> drop into **M30** to learn what pointers really are at the hardware level, and
> **M44** for production-grade modern C++.

**Prerequisites:** None beyond being able to open a terminal. If you've written any
code in any language (variables, loops, functions), you'll move fast; if not, you'll
still be fine — each concept is introduced from scratch.

**What you'll learn:**
- **The compile→run cycle**: source text → `clang`/`clang++` → a native executable
  (no interpreter, unlike Python)
- **C fundamentals**: static types & `sizeof`, `printf` format specifiers, `if`/
  `for`/`while`, functions and **pass-by-value**
- **Arrays and C strings**: fixed-size runs of one type, and the `'\0'`-terminated
  `char` array that is a C string
- **Pointers, structs, and the heap**: `&`/`*`, mutating a caller's variable through
  a pointer, `struct` with `.`/`->`, and `malloc`/`free`
- **The jump to C++**: `std::cout`, `std::string`, **references** vs pointers,
  `auto`, `std::vector`, a **class with RAII** (constructor/destructor), and a first
  **template**

> **Format:** like the rest of the CS Foundations track, this is real source + a
> `Makefile` + this lab — **no jupyter**. Demos 1–4 are **C** (`.c`), demos 5–6 are
> **C++** (`.cpp`). Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Runs **natively on Apple Silicon** (arm64) — no container needed. You need `clang`
(for C) and `clang++` (for C++); on macOS both ship with the Xcode Command Line
Tools:

```bash
clang --version                       # Apple clang, ships with Xcode CLT
make run                              # build + run all six demos
```

The `.c` files compile with `clang -std=c11 -Wall -Wextra -Wpedantic -g` and the
`.cpp` files with `clang++ -std=c++17 ...` — the one `Makefile` picks the right
compiler per file extension. Builds the same on Linux (`gcc`/`g++`). Zero warnings on
the whole module.

---

## 1. Your first program (and how it gets built)

A C program is just text; the **compiler** turns it into a native executable your CPU
runs directly. [`01_hello.c`](01_hello.c) is the smallest useful program: `#include
<stdio.h>` pulls in `printf`, `int main(void)` is where execution starts, and
`return 0` tells the OS "success." `make run1` compiles it (`clang -std=c11 -o
bin/01_hello 01_hello.c`) and runs it:

```
── demo 1 ──
Hello, C!
This program was compiled to a native executable.
```

That two-step — **compile, then run** — is the whole game. `make` just automates the
compile line for you.

## 2. Values and decisions

C is **statically typed**: every variable has a fixed type known at compile time, and
each type has a fixed size in bytes. `printf` uses **format specifiers** to render a
value — `%d` (int), `%f` (double), `%c` (char), `%zu` (a size). Then the three
control-flow tools you'll use forever: `if`/`else`, `for`, `while`.
[`02_types_control.c`](02_types_control.c) (`make run2`):

```
── demo 2 ──
=== types & sizeof ===
  int is 4 bytes, double is 8, char is 1
  x=7  pi=3.14159  grade='A'  ready=true
=== control flow: first 5 FizzBuzz ===
  1 2 Fizz 4 Buzz 
=== while countdown ===
  3 2 1 liftoff
```

`sizeof` reports how many bytes a type occupies. The FizzBuzz loop is `if`/`else if`
chains inside a `for`; the countdown is the same idea with a `while` and a decrement.

## 3. Reusable code, lists, and text

A **function** packages logic behind a name. In C, arguments are passed **by value** —
the function receives a *copy*, so writing to a plain parameter never touches the
caller's variable (Demo 4 shows how pointers get around that). An **array** is a
fixed-size run of one type; a **C string** is just a `char` array ending in a `'\0'`
terminator byte. [`03_functions_arrays.c`](03_functions_arrays.c) (`make run3`):

```
── demo 3 ──
=== functions ===
  square(6) = 36
  sum([1,2,3,4,5]) = 15
=== arrays ===
  max of {4, 9, 2, 7, 1} = 9
=== C strings (char arrays) ===
  "hello" reversed is "olleh"  (length 5)
```

`square`, `sum`, and `max_of` each take arguments and return a value; `sum`/`max_of`
walk an array with a `for` loop. `reverse_string` swaps characters in place — note it
*can* change the string because you hand it the array (which decays to a pointer),
the exact idea Demo 4 makes explicit.

## 4. The heart of C: pointers, structs, and the heap

A **pointer** is a variable that holds the **address** of another value. `&x` is
"address of `x`"; `*p` is "the value `p` points at" (dereference). Passing an address
lets a function change the caller's variable — the payoff missing from Demo 3. A
**struct** groups related fields; reach them with `.` on a value or `->` through a
pointer. **`malloc`** grabs memory from the **heap** that lives until you `free` it —
every `malloc` needs exactly one `free`. [`04_pointers_structs.c`](04_pointers_structs.c)
(`make run4`):

```
── demo 4 ──
=== pointers ===
  x = 10, &x is an address, *(&x) = 10
  after add_one(&x): x = 11
=== structs ===
  Point{ x=3, y=4 }  distance-from-origin squared = 25
=== malloc/free: a heap array of 5 ints ===
  heap[0..4] = 0 10 20 30 40
  freed. (every malloc needs exactly one free)
```

`add_one(&x)` mutates `x` back in `main` because it receives the *address*, not a
copy. `dist_sq_from_origin` reads struct fields through a pointer with `->`. The heap
array is sized at runtime and released with `free`. This is the *operational* view —
for the full stack/heap/memory model at the hardware level, that's
[Module 30 — C Programming I](../30_c_programming_i/).

## 5. The same ideas, in C++

C++ is C plus higher-level tools. [`05_hello_cpp.cpp`](05_hello_cpp.cpp) rewrites the
last two demos more safely: `std::cout <<` streams output (no format strings),
`std::string` is a real string (no `'\0'` bookkeeping, grows itself), a **reference**
`int&` is an alias for a variable — like a pointer that can't be null and needs no
`*` — `auto` lets the compiler deduce types, and `std::vector<int>` is a growable
array that frees its own memory. `make run5`:

```
── demo 5 ──
=== cout and std::string ===
  Hello, C++!  name = "Ada", length 3
=== references: an alias, no pointers needed ===
  before: n = 5
  after add_one(n): n = 6
=== std::vector: a growable array, freed for you ===
  v = 1 2 3 4  (size 4)
  sum via range-for = 10
```

Compare `add_one(int& n)` here with `add_one(int *p)` in Demo 4 — same effect, no `&`
at the call site and no `*` inside. The `range-for` (`for (auto x : v)`) walks the
vector without indices. Same `make`, different compiler under the hood: `.cpp` builds
with `clang++ -std=c++17`.

## 6. Your own type that cleans up after itself

A **class** bundles data with the functions that operate on it. Two special members
run **automatically**: the **constructor** when an object is created, and the
**destructor** when it goes out of scope. Tying cleanup to the destructor is called
**RAII** — compare Demo 4, where you must remember to `free`; here cleanup happens on
its own at scope exit, on every path. **Templates** let one definition serve many
types (a taste of what powers `std::vector`).
[`06_class_raii.cpp`](06_class_raii.cpp) (`make run6`):

```
── demo 6 ──
=== a class with RAII (constructor/destructor) ===
  [Counter] constructed (count=0)
  tick -> 1
  tick -> 2
  leaving scope...
  [Counter] destructed at count=2  (no free() needed — the destructor ran automatically)
=== a tiny template: one max_of for any type ===
  max_of(3, 9)     = 9
  max_of(2.5, 1.5) = 2.5
```

Watch the destructor fire the instant `c` leaves its scope — no cleanup call in
sight. `max_of` is written once and works for `int` and `double` because the compiler
stamps out a type-checked copy per type. For smart pointers, the STL in depth, and the
**rule of five**, continue to [Module 44 — C++ for Systems](../44_cpp_for_systems/).

---

## 7. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`. The stubs
compile and run out of the box (with placeholder output) so you always start from a
working build.

### Exercise 47.1 — Celsius to Fahrenheit  (`make ex1`)
Implement `celsius_to_fahrenheit(double c)` in
[`exercises/ex1_temperature.c`](exercises/ex1_temperature.c) using `F = C*9/5 + 32`
(watch out: use `9.0/5.0` for floating-point division). Expected (`make sol1`):
```
=== C -> F table ===
     0C =   32.0F
    20C =   68.0F
    37C =   98.6F
   100C =  212.0F
```

### Exercise 47.2 — Count the words in a string  (`make ex2`)
Implement `count_words(const char *s)` in
[`exercises/ex2_word_count.c`](exercises/ex2_word_count.c): scan the string and count
each transition from whitespace into a word. `isspace()` (from `<ctype.h>`) tells you
if a char is whitespace. Expected (`make sol2`):
```
=== word count ===
  text: "the quick brown fox jumps"
  words = 5
```

### Exercise 47.3 — A little stack class  (`make ex3`)
Finish `push`, `pop`, and `size` of the `IntStack` class in
[`exercises/ex3_stack_class.cpp`](exercises/ex3_stack_class.cpp), backed by a
`std::vector<int>` (`push_back`, `back`, `pop_back`, `size`). Expected (`make sol3`):
```
=== IntStack ===
  push 10, 20, 30  -> size 3
  pop -> 30
  pop -> 20
  size now 1
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **Compile → run** | C/C++ become native executables ahead of time — no interpreter at runtime |
| **Static types & `sizeof`** | Types are fixed and sized at compile time; the compiler checks your use |
| **Functions & pass-by-value** | Reuse logic; know that C copies arguments unless you pass an address |
| **Arrays & C strings** | Fixed runs of one type; a string is a `'\0'`-terminated `char` array |
| **Pointers, structs, `malloc`/`free`** | Addresses let you mutate and share data; the heap holds runtime-sized memory you must free |
| **C++ `cout`/`string`/`vector`/references** | The same tasks, shorter and memory-safe, with self-managing containers |
| **Classes & RAII** | Constructors/destructors run automatically — cleanup you can't forget |
| **Templates** | One definition, many types — the basis of the C++ standard library |

## Further reading

- **Brian Kernighan & Dennis Ritchie — *The C Programming Language* (2nd ed.)**: the
  classic, tiny, still-the-best C book, from the language's authors.
- **Bjarne Stroustrup — *A Tour of C++* (3rd ed.)**: the fastest accurate overview of
  modern C++ from its creator — the natural next step after demos 5–6.
- **cppreference** — the reference for both languages' standard libraries, with
  runnable examples: https://en.cppreference.com/

**Next:** you now know enough C and C++ to read and write real programs. To go deeper,
drop into the systems track: [**Module 30 — C Programming I**](../30_c_programming_i/)
for pointers and memory at the hardware level, then
[**Module 44 — C++ for Systems**](../44_cpp_for_systems/) for smart pointers, the STL,
and modern C++. When you want to call your C/C++ from Python, see
[**Module 45 — C/C++ ↔ Python**](../45_c_python_bridge/). See
[the track plan](../cs-foundations-track.md) for the full map.
