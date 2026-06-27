# Module 32 — Assembly & the ISA

**Purpose:** Under every C program is a stream of machine instructions the CPU
actually executes. This module makes that layer concrete: you'll read the assembly
the compiler generates, learn the **registers**, the **calling convention** (how
arguments and return values travel between functions), and **stack frames** (how
`call`/`return` and locals work). Two ISAs appear side by side — **x86-64**, the one
CS:APP teaches and the Bomb/Attack labs target, and **AArch64 (arm64)**, the ISA of
this very Mac, which you'll hand-write and run. Reading assembly is the skill behind
debugging optimized code, reverse engineering, exploitation, and understanding what
"the compiler did to my code."

**Prerequisites:** Module 31 (multi-file builds, the toolchain, `lldb`). Module 28
(bits/bytes/hex) helps for reading register values.

**What you'll learn:**
- How to get assembly from C (`clang -S`, `gcc -S`, `objdump -d`) and read a
  **prologue/epilogue**, a loop, and a `bl`/`call`
- The **register file** and the **System V (x86-64)** vs **AAPCS (arm64)** calling
  conventions — argument registers, the return register, caller- vs callee-saved
- **Stack frames**: where the saved **return address** and **frame pointer** live,
  and why a *leaf* function needs no frame
- How to **hand-write a native arm64 function** and link it into a C program
- How to run the **CS:APP Bomb Lab and Attack Lab** in the x86-64 container

> **Format:** real code, not notebooks. Source files + a `Makefile` + this lab. Build
> with `make`, run a demo with `make run1`, see generated assembly with `make asm1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

This Mac is **arm64 (Apple Silicon)**. The AArch64 demos and exercises here
**assemble and run natively** — just `clang` + `make` (Xcode Command Line Tools):

```bash
make run          # build + run the three native demos
make asm1         # write the native arm64 assembly for demo 1 to 01_compile_down.s
```

**CS:APP teaches x86-64, and you cannot assemble or run x86-64 natively on this Mac.**
So the textbook's **Bomb Lab** and **Attack Lab** (and any `objdump` that must match
the book byte-for-byte) run in the **x86-64 Linux container** from Module 28's
[`setup/README.md`](../28_bits_and_bytes/setup/README.md). Anything in this lab marked
**"x86-64 container — not run on this Mac"** is documentation only; the native parts
below show **real captured output** from this machine.

---

## 1. Compiling C down to assembly

The compiler translates C into instructions. The smallest way to *see* this is
`clang -S`, which stops after generating assembly. [`01_compile_down.c`](01_compile_down.c)
holds a recursive `factorial`, a `sum_to` loop, and a `main` that calls them.

```
make run1
```
```
── demo 1: C → asm ──
factorial(5)  = 120  (expected 120)
factorial(10) = 3628800  (expected 3628800)
sum_to(100)   = 5050  (expected 5050)
```

Now generate the **native arm64 assembly** (`make asm1` writes `01_compile_down.s`):

```
make asm1
```

Here is the **real** `main` clang emits at `-O1` on this Mac — a textbook
prologue/epilogue:

```asm
_main:
        sub     sp, sp, #32             ; allocate a 32-byte stack frame (stack grows DOWN)
        stp     x29, x30, [sp, #16]     ; PROLOGUE: save frame pointer (x29) + return addr (x30)
        add     x29, sp, #16            ; set x29 to the base of this frame
        mov     w0, #5                  ; arg 1 = 5  -> goes in x0/w0 (the 1st arg register)
        bl      _factorial              ; call; `bl` puts the return address in x30
        str     x0, [sp]                ; factorial returned in x0; stash it for printf
        adrp    x0, l_.str@PAGE         ; load address of the format string (2-instr on arm64)
        add     x0, x0, l_.str@PAGEOFF
        bl      _printf
        ...
        mov     w0, #0                  ; return 0 from main
        ldp     x29, x30, [sp, #16]     ; EPILOGUE: restore x29/x30
        add     sp, sp, #32             ; deallocate the frame
        ret                             ; branch to the address in x30
```

What to notice, all visible above:
- **Prologue/epilogue** — `stp`/`ldp` save and restore the **frame pointer `x29`** and
  the **return address `x30`** (the *link register*, `lr`). `main` is a non-leaf
  function (it calls `factorial`/`printf`), so it *must* preserve `x30` — see §4.
- **The stack grows downward** — `sub sp, sp, #32` allocates; `add sp, sp, #32` frees.
- **`bl`** ("branch with link") is the call: it jumps **and** records the return
  address in `x30`. `ret` jumps to whatever is in `x30`.
- **Arguments go in registers** — `mov w0, #5` puts the argument in `x0` before the call.

Even more instructive: at `-O1` the optimizer **rewrote the algorithms**. `factorial`
became a *loop* (tail-recursion → iteration), and `factorial(5)`/`sum_to(100)` were
**constant-folded** — `main` just loads the literal `#5050` (`0x13ba`) instead of
running the loop. Optimized assembly rarely matches the source line-for-line; that gap
is exactly why reading asm is a skill.

> **To get x86-64 assembly (in the container):** `gcc -O1 -S -masm=intel 01_compile_down.c`
> (`-masm=intel` for the Intel syntax CS:APP and most tooling use; drop it for AT&T
> syntax). Or disassemble a built binary with `objdump -d`. Run this in the Module 28
> x86-64 box — **not on this Mac**. [Godbolt](https://godbolt.org/) shows both ISAs
> side by side in the browser.

## 2. A hand-written native arm64 function

To prove the calling convention is a real, callable contract, [`02_add.s`](02_add.s)
is a **leaf** function written by hand in AArch64 assembly and called from C in
[`02_add_main.c`](02_add_main.c):

```asm
.global _add_asm
_add_asm:
        add     x0, x0, x1      ; x0 = a + b  (a came in x0, b in x1, result stays in x0)
        ret                     ; return to caller via x30
```

The C side just declares `long add_asm(long, long);` — the compiler type-checks the
call and the **linker** resolves it to the `_add_asm` label (Apple symbols get a
leading underscore). No stack frame is needed because a **leaf function calls nothing**,
so `x30` is never clobbered. `make run2` assembles `.s`, compiles the C, links them,
and runs — **real output from this Mac:**

```
make run2
```
```
── demo 2: hand-written arm64 add_asm ──
add_asm(2, 3)      = 5  (expected 5)
add_asm(100, 23)   = 123  (expected 123)
add_asm(-5, 5)     = 0  (expected 0)
```

That is genuine hand-written assembly executing on Apple Silicon — the entire body is
two instructions.

## 3. The calling convention (and the side-by-side table)

The **calling convention** is the ABI contract: which registers carry which argument,
where the return value lands, who must preserve what. [`03_calling_convention.c`](03_calling_convention.c)
exercises the edges — nine integer args (more than fit in registers) and a struct
returned by value.

```
make run3
```
```
── demo 3: calling convention ──
sum9(1..9) = 45  (expected 45)
make_point(3, 4) = {x=3, y=4}
```

`make asm3` writes `03_calling_convention.s`. The **real** `sum9` body proves where
the arguments live:

```asm
_sum9:
        ldr     x8, [sp]        ; the 9th argument was passed ON THE STACK
        add     x9, x1, x0      ; the first 8 arrived in registers x0..x7
        add     x10, x2, x3
        ...
        add     x9, x9, x7      ; ...x7 is the 8th
        add     x0, x9, x8      ; total returns in x0
        ret
```

The first eight integer arguments ride in **x0–x7**; the ninth spills to the **stack**,
which `sum9` reads with `ldr x8, [sp]`. The sum returns in **x0**.

### x86-64 (System V) vs arm64 (AAPCS) — register & convention map

| Role | **x86-64 (System V ABI)** | **arm64 (AAPCS)** |
|------|---------------------------|--------------------|
| Integer/pointer args 1–6 / 1–8 | `rdi, rsi, rdx, rcx, r8, r9` (6) | `x0, x1, x2, x3, x4, x5, x6, x7` (8) |
| Further integer args | on the **stack** | on the **stack** (after x0–x7) |
| Integer return value | `rax` (and `rdx` for 128-bit) | `x0` (and `x1` for 16-byte structs) |
| Floating-point args / return | `xmm0`–`xmm7` / `xmm0` | `v0`–`v7` / `v0` |
| Return address | pushed on stack by `call` | in `x30` (link register) by `bl` |
| Frame pointer | `rbp` | `x29` (FP) |
| Stack pointer | `rsp` | `sp` |
| Callee-saved (you must preserve) | `rbx, rbp, r12–r15` | `x19–x28, x29, x30` |
| Caller-saved (clobberable) | `rax, rcx, rdx, rsi, rdi, r8–r11` | `x0–x18` |
| Call / return instruction | `call` / `ret` | `bl` / `ret` |
| Stack alignment at a call | 16 bytes | 16 bytes |

The two conventions are the same *idea* — first few args in registers, rest on the
stack, one return register — differing mainly in **how many** arg registers (6 vs 8)
and that arm64 keeps the **return address in a register (`x30`)** rather than pushing
it, which is why arm64 leaf functions can skip the stack entirely.

## 4. Stack frames, leaf vs non-leaf

Putting §1 and §2 together: a function's **frame** holds its saved registers and
locals. On arm64 the prologue you saw in §1,

```asm
stp     x29, x30, [sp, #-16]!   ; push the caller's frame pointer + the return address
mov     x29, sp                 ; this function's frame base
```

saves **`x30` (the return address)** and **`x29` (the caller's frame pointer)**, then
points `x29` at the new frame. The matching epilogue (`ldp … ; ret`) restores them and
returns. A **non-leaf** function *must* do this, because its own `bl` overwrites `x30`;
a **leaf** function (`add_asm`, `max2`) calls nothing, so `x30` survives and **no frame
is needed**. Exercise 32.3 walks a frame instruction-by-instruction.

## 5. The CS:APP Bomb Lab & Attack Lab  (x86-64 container — *not run on this Mac*)

The flagship challenges for this material are CS:APP's:

- **Bomb Lab** — a binary that `explode_bomb`s unless you feed each of six phases the
  right input. You defuse it by **disassembling** (`objdump -d bomb`), reading the
  x86-64, and stepping in `gdb` — the exact skills from §1–§4 applied to code you do
  *not* have the source for.
- **Attack Lab** — craft inputs that exploit buffer overflows to redirect control flow
  (code injection and return-oriented programming). It makes stack frames and return
  addresses viscerally real.

**These are x86-64 and must run in the x86-64 container** (their bytes and addresses
assume the x86-64 ABI; they will neither assemble nor execute on arm64):

```bash
# from the repo root, start the Module 28 x86-64 box:
docker run --platform=linux/amd64 -it -v "$PWD":/work csfoundations
# inside the container (Linux x86-64):
cd /work/32_assembly
# download a self-study bomb from the CS:APP labs page, then:
objdump -d bomb | less        # disassemble; read the x86-64 for each phase
gdb ./bomb                     # break explode_bomb; step phases; inspect %rdi etc.
```

Get the labs (self-study writeups + binaries) from the CS:APP labs page:
**http://csapp.cs.cmu.edu/3e/labs.html**. Use `gdb` (commands as in Module 31 §5),
`objdump -d`, and the System V column of the table above.

> *Output for the bomb/attack labs is intentionally not shown — these run in the
> container, not on this Mac, and each bomb is per-student. The native sections above
> are the parts with captured real output.*

---

## 6. Exercises

Each lives in `exercises/`; reference answers in `solutions/`. Exercise 1 builds and
runs natively; 2 and 3 are paper (reading/tracing) exercises.

### Exercise 32.1 — Hand-write an arm64 `max2`  (`make ex1`)
Implement `long max2(long, long)` in AArch64 assembly in
[`exercises/ex1_max2.s`](exercises/ex1_max2.s) using `cmp` + a conditional branch
(`b.ge`). The driver is given. The stub returns wrong values until you fill it in;
the solution (`make sol1`) prints:
```
max2(3, 7)   = 7  (expected 7)
max2(9, 2)   = 9  (expected 9)
max2(-5, -1) = -1  (expected -1)
max2(4, 4)   = 4  (expected 4)
```

### Exercise 32.2 — Read the assembly, predict the result  (paper)
Read an `clang -O1 -S` arm64 snippet in
[`exercises/ex2_read_asm.md`](exercises/ex2_read_asm.md) and predict what the function
returns. Solution: [`solutions/ex2_read_asm.md`](solutions/ex2_read_asm.md).

### Exercise 32.3 — Trace a stack frame  (paper)
Given a non-leaf arm64 prologue/epilogue in
[`exercises/ex3_stack_frame.md`](exercises/ex3_stack_frame.md), identify the saved
return address and frame pointer and explain the return. Solution:
[`solutions/ex3_stack_frame.md`](solutions/ex3_stack_frame.md).

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **C → assembly (`clang -S`, `gcc -S`, `objdump`)** | The only way to see what the CPU runs; optimized asm rarely matches source — reading it is a real skill |
| **Registers & the register file** | Instructions operate on a few named registers; everything else is memory traffic |
| **Calling conventions (System V vs AAPCS)** | The ABI contract: args in registers then stack, value in the return register — lets C, asm, and libraries interoperate |
| **Stack frames, prologue/epilogue** | Where the saved return address and frame pointer live; how `call`/`ret` and locals work; leaf functions need no frame |
| **Hand-written assembly linked with C** | Demystifies the boundary — a function is just a label, a calling convention, and a `ret` |
| **Bomb/Attack Lab (x86-64)** | Applying all of the above to binaries you can't read the source of — debugging, reversing, exploitation |

## Further reading

- **CS:APP3e, Chapter 3 — Machine-Level Representation of Programs** (the definitive
  treatment of x86-64 assembly, the stack, and the calling convention): http://csapp.cs.cmu.edu/
- **CS:APP Bomb Lab & Attack Lab** (the gated challenges for this module — run in the
  x86-64 container): http://csapp.cs.cmu.edu/3e/labs.html
- **MIT 6.191 (formerly 6.004) Computation Structures** (the course this track's Phase
  A follows; ISA and assembly lectures):
  https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/
- **Compiler Explorer (Godbolt)** — type C, see x86-64 *and* arm64 assembly update
  live, side by side: https://godbolt.org/
- **Arm A64 Instruction Set Architecture reference** (the AArch64 mnemonics used in
  this module): https://developer.arm.com/documentation/ddi0596/latest

**Next:** Module 33 — Computer Architecture — pipelining & hazards, the memory
hierarchy, cache-timing experiments, and locality, with the CS:APP Cache Lab
(CS:APP ch.5–6; MIT 6.191). *(Not yet built — see [the track plan](../cs-foundations-track.md);
the lab will live at [../33_architecture/README.md](../33_architecture/README.md).)*
