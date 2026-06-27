# Module 29 — Digital Logic & the CPU

**Purpose:** A computer is, underneath everything, a pile of switches wired together.
This module shows you *how* — by building digital logic up from a **single NAND gate**
(the Nand2Tetris idea), in plain C so it runs natively and every claim is verifiable
from printed output. This is the second module of the **CS Foundations track**, and its
deliverable is **a working gate/logic simulator** that climbs from one primitive to an
ALU with status flags — the arithmetic heart of a CPU.

**Prerequisites:** **Module 28** (bits, bytes, two's complement). The subtraction demo
and the ALU lean directly on two's complement from there; if `~b + 1 == -b` isn't yet
reflexive for you, do Module 28 first.

**What you'll learn:**
- Why **NAND is universal**: NOT, AND, OR, XOR all built from that one gate
- The **multiplexer** — "choose a wire" — and why it's the seed of selection/branching
- How **binary addition** is wired: half adder → full adder → ripple-carry adder
- That **subtraction is just addition** of the two's complement (one adder does both)
- How a tiny **ALU** computes add/sub/and/or and derives **zero/negative flags**, and
  how registers + a control loop turn it into a CPU (conceptually)

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 29 runs **natively on Apple Silicon** (arm64) — no container, no HDL toolchain.
It's a pure *software* gate simulator: you only need `clang` + `make` (Xcode Command
Line Tools).

```bash
make run        # build + run all four demos
```

Each demo defines `nand()` as its only primitive and builds everything else from it,
so the files are self-contained and you can read any one start to finish.

---

## 1. NAND is universal

A **logic gate** is a function from input bits to an output bit. The remarkable fact:
you need only **one** of them — **NAND** (`NOT(a AND b)`) — to build every other gate,
and from there, an entire computer. [`01_gates.c`](01_gates.c) defines `nand()` as the
sole primitive and constructs the rest:

- `NOT a = NAND(a, a)` — tie both inputs together
- `AND a b = NOT(NAND(a, b))` — undo NAND's built-in inversion
- `OR a b = NAND(NOT a, NOT b)` — De Morgan's law
- `XOR a b = NAND(NAND(a, NAND(a,b)), NAND(b, NAND(a,b)))` — the 4-NAND classic

```
make run1
```
```
=== The one primitive: NAND ===
  NAND:  a b | out
        0 0 |  1
        0 1 |  1
        1 0 |  1
        1 1 |  0

=== Built from NAND only ===
  NOT :  a | out
        0 |  1
        1 |  0

  AND :  a b | out
        0 0 |  0
        0 1 |  0
        1 0 |  0
        1 1 |  1

  OR  :  a b | out
        0 0 |  0
        0 1 |  1
        1 0 |  1
        1 1 |  1

  XOR :  a b | out
        0 0 |  0
        0 1 |  1
        1 0 |  1
        1 1 |  0
```

Because NAND is *functionally complete*, a whole CPU can be built from this one block —
which is exactly what the rest of this module does, one layer at a time.

## 2. The multiplexer — selection in hardware

A **multiplexer** (mux) passes one of several inputs through, chosen by a *select*
signal. It is the hardware form of `if`/`else` and of array indexing: whenever a CPU
decides *which* value flows onto a bus, a mux is doing it. [`02_mux.c`](02_mux.c)
(`make run2`) builds a 2:1 mux from gates, a 4:1 mux as a *tree* of 2:1 muxes, and the
inverse — a 1-bit **demux** that routes one input to one of two outputs:

```
=== 2:1 mux: out = (sel ? b : a) ===
  a b sel | out
  0 0  0  |  0
  0 1  0  |  0
  1 0  0  |  1
  1 1  0  |  1
  0 0  1  |  0
  0 1  1  |  1
  1 0  1  |  0
  1 1  1  |  1

=== 4:1 mux: (s1 s0) selects one of a,b,c,d ===
  inputs a=0 b=1 c=0 d=1
  s1 s0 | picks | out
   0  0 |   a   |  0
   0  1 |   b   |  1
   1  0 |   c   |  0
   1  1 |   d   |  1

=== 1-bit demux: route `in` to out0 or out1 ===
  in sel | out0 out1
  0   0  |   0    0
  0   1  |   0    0
  1   0  |   1    0
  1   1  |   0    1
```

`2:1 mux = (a AND NOT sel) OR (b AND sel)` — "let `a` through when `sel`=0, `b` when
`sel`=1". Wider muxes are just trees of these. This is the seed of conditional
execution; a branch is ultimately a mux choosing the next instruction address.

## 3. Binary addition — half adder → full adder → ripple carry

Addition is the first real arithmetic we can wire up. [`03_adder.c`](03_adder.c)
(`make run3`) builds it in three layers, all from gates:

- **half adder** — adds two bits: `sum = a XOR b`, `carry = a AND b`
- **full adder** — adds two bits **plus a carry-in** (two half adders + an OR)
- **ripple-carry adder** — chain N full adders, the carry rippling LSB→MSB

```
=== Half adder (a + b) ===
  a b | sum carry
  0 0 |  0    0
  0 1 |  1    0
  1 0 |  1    0
  1 1 |  0    1

=== Full adder (a + b + carry-in) ===
  a b cin | sum cout
  0 0  0  |  0    0
  0 0  1  |  1    0
  0 1  0  |  1    0
  0 1  1  |  0    1
  1 0  0  |  1    0
  1 0  1  |  0    1
  1 1  0  |  0    1
  1 1  1  |  1    1

=== 4-bit ripple-carry add: 5 + 6 ===
    0101  (5)
  + 0110  (6)
  = 1011  (11)   carry-out=0

=== 4-bit overflow: 12 + 5 wraps (only 4 bits to hold it) ===
  12 + 5 = 1  carry-out=1  (17 needs a 5th bit -> wraps to 1)

=== 8-bit ripple-carry add: 100 + 27 ===
  01100100 + 00011011 = 01111111  (127, carry=0)

=== Subtraction via two's complement: 9 - 4 (8-bit) ===
       a = 00001001  (9)
      ~b = 11111011
  a+~b+1 = 00000101  (5)   (carry-out=1 discarded)
  -> 9 - 4 = 5
```

The payoff ties back to Module 28: **subtraction is addition of the two's complement**.
`a - b == a + (~b + 1)`. Invert `b`'s bits and feed the ripple adder a carry-**in** of
1 (that supplies the `+1` for free) — the *same* adder now subtracts. No separate
subtractor circuit exists; this is *why* hardware uses two's complement.

## 4. A tiny ALU — the heart of the datapath

An **ALU** (Arithmetic Logic Unit) takes two N-bit operands plus a few control bits and
produces a result + status flags. [`04_alu.c`](04_alu.c) (`make run4`) builds an 8-bit
ALU with a 2-bit op-select (`00`=AND, `01`=OR, `10`=ADD, `11`=SUB) and two flags:
**ZERO** (result is all zeros — an OR-reduce, then invert) and **NEGATIVE** (the sign
bit). Note the design: it computes *all four* candidate results in parallel and a
per-bit mux selects the chosen one — exactly how real hardware works.

```
=== Tiny 8-bit ALU: operands a=20, b=5 ===
  a = 00010100  (20)
  b = 00000101  (5)

  op  name | result          uns  sgn | Z N
  00  AND | 00000100    4     4 | 0 0
  01  OR  | 00010101   21    21 | 0 0
  10  ADD | 00011001   25    25 | 0 0
  11  SUB | 00001111   15    15 | 0 0

=== Flags in action: 7 - 7 sets ZERO; 5 - 9 sets NEGATIVE ===
  7 - 7 = 0   Z=1 N=0
  5 - 9 = -4  Z=0 N=1
```

### 5. From ALU to CPU (the honest scope)

This module stops at the ALU — it does **not** simulate a full CPU. But you now have all
the combinational pieces, and the rest is conceptually short:

- **Registers** store bits across clock ticks. The storage element is a **flip-flop**
  (built from gates with feedback); a register is a row of them. Combinational logic
  alone has no memory — feedback + a clock is what adds state.
- The **datapath** wires registers to the ALU: read operands from registers, run them
  through the ALU, write the result back.
- The **control unit** runs the **fetch-decode-execute loop**: *fetch* the next
  instruction from memory (the program counter says where), *decode* it into ALU op +
  register selects (those become the mux/op-select bits you just used), *execute* it,
  then advance the program counter — and the ALU's **ZERO**/**NEGATIVE** flags are what
  conditional branches test.

Building the registers, memory, and control unit to run actual machine code is the
back half of Nand2Tetris (projects 3–5) and the subject of the next modules.

---

## 6. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`.

### Exercise 29.1 — A 3-input AND from gates  (`make ex1`)
Implement `and3` in [`exercises/ex1_and3.c`](exercises/ex1_and3.c) using only the
provided gates (`and3 = AND(AND(a,b), c)`). Expected (`make sol1`):
```
  a b c | out
  0 0 0 |  0
  0 0 1 |  0
  0 1 0 |  0
  0 1 1 |  0
  1 0 0 |  0
  1 0 1 |  0
  1 1 0 |  0
  1 1 1 |  1
```

### Exercise 29.2 — An 8-bit ripple-carry adder  (`make ex2`)
Implement `add8` in [`exercises/ex2_add_bytes.c`](exercises/ex2_add_bytes.c) by chaining
8 full adders. Watch the carry-out flag flip when a sum exceeds 255. Expected
(`make sol2`):
```
  01100100 + 00011011 = 01111111  (100 + 27 = 127, carry=0)
  11001000 + 01100100 = 00101100  (200 + 100 = 44, carry=1)
  11111111 + 00000001 = 00000000  (255 + 1 = 0, carry=1)
```

### Exercise 29.3 — An equality comparator from gates  (`make ex3`)
Implement `equal4` in [`exercises/ex3_equal.c`](exercises/ex3_equal.c): XOR each bit
pair (1 where they differ), OR-reduce the differences, then invert. Expected
(`make sol3`):
```
   a  b | equal?
   5  5 |   1
   5  7 |   0
   0  0 |   1
  15 14 |   0
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **NAND is universal** | One gate (functionally complete) builds NOT/AND/OR/XOR and, ultimately, a whole CPU |
| **Multiplexer / demux** | "Choose a wire" — the hardware form of selection, indexing, and branching |
| **Half / full adder** | The wiring of binary addition: `sum = XOR`, `carry = AND`, plus a carry-in chain |
| **Ripple-carry adder** | N full adders chained; carry flows LSB→MSB exactly like adding on paper |
| **Subtraction = add two's complement** | `a - b = a + ~b + 1` — one adder does both; the reason hardware uses two's complement |
| **ALU + flags** | Add/sub/and/or with ZERO/NEGATIVE flags — the datapath block that computes, and what branches test |

## Further reading

- **Nand2Tetris** — *The Elements of Computing Systems* (Nisan & Schocken): build a full
  computer from a NAND gate up to an OS. This module is its projects 1–3 in C:
  https://www.nand2tetris.org/
- **MIT 6.191 (formerly 6.004) Computation Structures** — gates, combinational &
  sequential logic, building a processor:
  https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/
- **CS:APP3e, Chapter 4 — Processor Architecture** — how the ALU, registers, and control
  fit into a working (Y86-64) CPU and pipeline: http://csapp.cs.cmu.edu/

**Next:** [Module 30 — C Programming I](../30_c_programming_i/README.md) — the memory
model, pointers, stack vs heap; build a dynamic array and a linked list in C.
*(Not yet built — see [the track plan](../cs-foundations-track.md).)*
