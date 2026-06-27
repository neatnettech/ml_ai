// Module 32 — Demo 2: a hand-written native AArch64 (arm64) leaf function
//
//   long add_asm(long a, long b);
//
// This is REAL assembly that assembles and runs on this Apple Silicon Mac. It is a
// "leaf" function — it calls nothing — so it needs no stack frame at all: it just
// uses the argument registers and returns.
//
// AAPCS (the arm64 calling convention):
//   - integer/pointer arguments arrive in x0, x1, x2, ... (first 8)
//   - the return value goes back in x0
//   - so add_asm(a, b) sees a in x0 and b in x1, and must leave the sum in x0.
//
// Assembled + linked + run by `make run2` (together with 02_add_main.c).

// On Apple platforms the assembler/linker expects a leading underscore on C symbols,
// so the C name `add_asm` is the assembly label `_add_asm`. The .p2align keeps the
// entry point on a 4-byte boundary (every arm64 instruction is exactly 4 bytes).
.global _add_asm
.p2align 2
_add_asm:
    add     x0, x0, x1      // x0 = x0 + x1  (a + b); result already in the return reg
    ret                     // return to caller (branches to the address in x30/lr)
