// Exercise 29.1 — A 3-input AND from gates
//
// Implement `and3(a, b, c)` that returns 1 only when ALL THREE inputs are 1,
// using ONLY the provided primitives (nand / gate_not / gate_and). The natural
// build is to AND two inputs, then AND the result with the third.
//
// Then `make ex1` should match the expected output in README.md §6.
// Solution in ../solutions/ex1_and3.c.

#include <stdio.h>

static int nand(int a, int b)     { return !(a && b); }
static int gate_not(int a)        { return nand(a, a); }
static int gate_and(int a, int b) { return gate_not(nand(a, b)); }

int and3(int a, int b, int c) {
    // TODO: return 1 only when a, b, and c are all 1, using gate_and (or nand).
    // Hint: and3 = AND( AND(a,b), c ).
    (void)a; (void)b; (void)c;  // remove once you use the inputs
    (void)gate_and;             // silences "unused" until you call it
    return 0;
}

int main(void) {
    printf("  a b c | out\n");
    for (int a = 0; a <= 1; a++)
        for (int b = 0; b <= 1; b++)
            for (int c = 0; c <= 1; c++)
                printf("  %d %d %d |  %d\n", a, b, c, and3(a, b, c));
    return 0;
}
