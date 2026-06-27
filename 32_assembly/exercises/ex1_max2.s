// Exercise 32.1 — hand-write a native arm64 leaf function
//
//   long max2(long a, long b);   // returns the larger of a and b
//
// a arrives in x0, b in x1; leave the result in x0 (AAPCS). This is a leaf function,
// so no stack frame is needed — just compare and branch. `make ex1` assembles this
// with the given driver ex1_max2_main.c and runs it. Solution in ../solutions/.
//
// Useful instructions:
//   cmp x0, x1        // sets condition flags from (x0 - x1)
//   b.ge LABEL        // branch to LABEL if x0 >= x1 (signed)
//   mov x0, x1        // x0 = x1
//   ret               // return (x0 holds the result)
// Pick a label name (e.g. Ldone) and prefix it as you like.

.global _max2
.p2align 2
_max2:
    // TODO: if a (x0) is already >= b (x1), return a; otherwise move b into x0.
    // Hint: cmp x0, x1 ; b.ge <done> ; mov x0, x1 ; <done>: ret
    ret
