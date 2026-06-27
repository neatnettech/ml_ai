// Module 32 — Demo 2 driver: call the hand-written arm64 add_asm from C
//
// The C compiler doesn't know or care that add_asm is written in assembly — it just
// needs a *declaration* (the prototype below) to type-check the call, and the linker
// resolves it to the label `_add_asm` in 02_add.s. This is exactly how C and asm are
// glued together. Build & run with `make run2`.

#include <stdio.h>

// Declared here, DEFINED in 02_add.s. The signature must match the registers the
// assembly uses: two longs in x0/x1, a long back in x0.
long add_asm(long a, long b);

int main(void) {
    printf("add_asm(2, 3)      = %ld  (expected 5)\n", add_asm(2, 3));
    printf("add_asm(100, 23)   = %ld  (expected 123)\n", add_asm(100, 23));
    printf("add_asm(-5, 5)     = %ld  (expected 0)\n", add_asm(-5, 5));
    return 0;
}
