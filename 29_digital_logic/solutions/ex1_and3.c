// SOLUTION 29.1 — A 3-input AND from gates

#include <stdio.h>

static int nand(int a, int b)     { return !(a && b); }
static int gate_not(int a)        { return nand(a, a); }
static int gate_and(int a, int b) { return gate_not(nand(a, b)); }

int and3(int a, int b, int c) {
    return gate_and(gate_and(a, b), c);  // AND( AND(a,b), c )
}

int main(void) {
    printf("  a b c | out\n");
    for (int a = 0; a <= 1; a++)
        for (int b = 0; b <= 1; b++)
            for (int c = 0; c <= 1; c++)
                printf("  %d %d %d |  %d\n", a, b, c, and3(a, b, c));
    return 0;
}
