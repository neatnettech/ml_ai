// SOLUTION 32.1 — native arm64 leaf function: long max2(long a, long b)
//
// a in x0, b in x1, result in x0 (AAPCS). Leaf function: no stack frame.

.global _max2
.p2align 2
_max2:
    cmp     x0, x1          // compare a - b, setting the condition flags
    b.ge    Lmax2_done      // if a >= b (signed), a is already the answer in x0
    mov     x0, x1          // else the answer is b; move it into the return register
Lmax2_done:
    ret                     // x0 holds max(a, b)
