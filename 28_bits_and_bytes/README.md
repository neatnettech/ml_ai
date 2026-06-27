# Module 28 — Bits, Bytes & Number Representation

**Purpose:** Everything a computer does is bytes, and every byte is 8 bits — so the
first step in understanding computers from the ground up is to *see* those bits and
know exactly what a given pattern means. This module is the foundation of the
**CS Foundations track**: you'll read the raw bits of integers and floats, understand
two's complement and IEEE-754, and manipulate bits directly in C — the skills every
later module (assembly, caches, the kernel) assumes.

**Prerequisites:** None — this is the starting module of the CS Foundations track.
Some prior programming helps, but no C is assumed; we introduce what we use.

**What you'll learn:**
- How to print the binary/hex of any value, and what *endianness* means
- **Two's complement**: how one bit pattern represents a negative number, and why overflow wraps
- **IEEE-754**: how a `float` is sign × mantissa × 2^exponent, and why `0.1 + 0.2 != 0.3`
- The **bitwise operators** (`& | ^ ~ << >>`) and the classic bit tricks built on them

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 28 runs **natively on Apple Silicon** — no container needed. You only need
`clang` + `make` (Xcode Command Line Tools), or the full track toolchain:

```bash
brew bundle --file=setup/Brewfile     # optional; see setup/README.md
make run                              # build + run all four demos
```

(The x86-64 container and RISC-V emulator in `setup/` are for later modules — see
[setup/README.md](setup/README.md).)

---

## 1. Bits, bytes, and types

A **bit** is one binary digit (0 or 1). A **byte** is 8 bits — the smallest unit a
program normally addresses. A C type is just a fixed number of bytes interpreted a
certain way. [`01_bit_patterns.c`](01_bit_patterns.c) prints the sizes and the bits:

```
make run1
```
```
=== One byte: the number 65 ('A') ===
  decimal 65, hex 0x41, char 'A', bits 01000001
```

The trick used everywhere in this module: cast any object to `unsigned char *` and
walk its bytes — the one cast the C standard blesses for inspecting raw memory.

## 2. Endianness

A multi-byte value has to be laid out in memory in *some* byte order. **Little-endian**
machines (x86-64, Apple Silicon) store the least-significant byte at the lowest
address. Demo 1 proves it on the int `0x0A0B0C0D`:

```
  the SAME int, byte-by-byte in MEMORY order (low address first):
  0x0D 0x0C 0x0B 0x0A
  -> first byte in memory is 0x0D => this machine is LITTLE-endian
```

This matters the moment you read a file format, a network packet, or a memory dump.

## 3. Two's complement (signed integers)

How does `11111111` mean `-1`? In **two's complement**, the top bit carries a
*negative* weight. The same 8 bits read as unsigned vs signed
([`02_twos_complement.c`](02_twos_complement.c), `make run2`):

```
  bits      unsigned   signed (two's complement)
  10000000   128        -128
  11111111   255          -1
```

Two consequences you must internalize:
- **Negation = flip the bits and add 1.** `5` → `~5` → `+1` → `-5`.
- **Overflow wraps around a ring**, not off a cliff: `INT8_MAX (127) + 1` → `-128`.
  (Signed overflow is *Undefined Behavior* in C — Module 31 — so the demo wraps in
  `unsigned`, which is defined, then reinterprets.)

## 4. IEEE-754 floating point

A `float` is **32 bits = 1 sign + 8 exponent + 23 mantissa**, meaning
sign × 1.mantissa × 2^(exponent−127). [`03_floats.c`](03_floats.c) (`make run3`) takes
floats apart:

```
  1             bits: 0 01111111 00000000000000000000000
               sign=0 exp=127 (unbiased 0) mantissa=0x000000
  0.1           bits: 0 01111011 10011001100110011001101
               sign=0 exp=123 (unbiased -4) mantissa=0x4CCCCD
```

`0.1` has no exact binary representation (note the repeating mantissa), which is why:

```
  0.1 + 0.2 = 0.30000000000000004
  == 0.3?   no
```

Special values fall out of the format: `exp` all-ones means **inf** (mantissa 0) or
**NaN** (mantissa nonzero), and `NaN == NaN` is **false**.

## 5. Bitwise operators

`& | ^ ~ << >>` operate on individual bits — the basis of flags, masks, permissions
(`chmod`!), and protocols. [`04_bitwise.c`](04_bitwise.c) (`make run4`) covers the
four single-bit ops and three classics:

```
  is 16 a power of two? yes          # x & (x-1) == 0
  popcount(00101100) = 3 set bits    # clear lowest set bit in a loop
  XOR-swapped 3 and 9 -> a=9 b=3     # XOR is its own inverse
```

- **set** `x | (1<<n)` · **clear** `x & ~(1<<n)` · **toggle** `x ^ (1<<n)` · **test** `(x>>n)&1`
- **mask** with `&` to extract fields; **shift** to multiply/divide by powers of two.

---

## 6. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`.

### Exercise 28.1 — Print a byte in binary  (`make ex1`)
Implement `print_byte` in [`exercises/ex1_print_byte.c`](exercises/ex1_print_byte.c).
Expected (`make sol1`):
```
  0 = 00000000
  1 = 00000001
 65 = 01000001
128 = 10000000
255 = 11111111
```

### Exercise 28.2 — Popcount  (`make ex2`)
Implement `count_bits` in [`exercises/ex2_count_bits.c`](exercises/ex2_count_bits.c).
Try both the simple 32-iteration loop and the `x & (x-1)` trick. Expected:
```
count_bits(0x00000000) = 0
count_bits(0xFFFFFFFF) = 32
count_bits(0x000000B4) = 4
```

### Exercise 28.3 — A float's sign from its bits  (`make ex3`)
Implement `is_negative` in [`exercises/ex3_float_sign.c`](exercises/ex3_float_sign.c)
using only the raw bits — so it reports `-0.0` as negative, which `f < 0` cannot:
```
is_negative(-3.5      ) = 1
is_negative(-0        ) = 1      <- the payoff: -0.0 has the sign bit set
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **Bit / byte / type sizes** | Every value is a fixed run of bytes; `sizeof` and `unsigned char *` let you inspect any of them |
| **Endianness** | Byte order decides how multi-byte values sit in memory — essential for files, packets, memory dumps |
| **Two's complement** | One scheme makes signed arithmetic work with the same adder as unsigned; explains negation and overflow wrap |
| **IEEE-754** | Floats are sign×mantissa×2^exp — finite precision, so equality and `0.1+0.2` surprise the unwary |
| **Bitwise ops & tricks** | set/clear/toggle/test, masks, shifts, popcount, power-of-two test — the vocabulary of low-level code |

## Further reading

- **CS:APP3e, Chapter 2 — Representing and Manipulating Information** (the definitive
  treatment; pairs with this module 1:1): http://csapp.cs.cmu.edu/
- **CS:APP Data Lab** (puzzles: implement ops using only bitwise primitives — the
  natural next challenge after the exercises here):
  http://csapp.cs.cmu.edu/3e/labs.html
- **MIT 6.191 (formerly 6.004) Computation Structures** (the course this track's
  Phase A follows): https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/
- **What Every Computer Scientist Should Know About Floating-Point Arithmetic**
  (Goldberg, the classic): https://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html

**Next:** Module 29 — Digital Logic & the CPU — build up from a single NAND gate to
gates, a mux, an ALU, and a tiny CPU that runs machine code (Nand2Tetris projects
1–5). *(Not yet built — see [the track plan](../cs-foundations-track.md).)*
