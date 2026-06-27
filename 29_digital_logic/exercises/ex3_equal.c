// Exercise 29.3 — An equality comparator from gates
//
// Implement `equal4(a, b)` that returns 1 iff two 4-bit numbers (arrays of int
// bits, index 0 = LSB) are equal, using ONLY gates. The idea:
//   - XOR each pair of bits: a[i] XOR b[i] is 1 exactly where the bits DIFFER.
//   - OR-reduce those differences: the OR is 1 if ANY bit differs.
//   - Invert: equal == NOT(any-difference).
//
// Then `make ex3` should match the expected output in README.md §6.
// Solution in ../solutions/ex3_equal.c.

#include <stdio.h>

#define N 4

static int nand(int a, int b)      { return !(a && b); }
static int gate_not(int a)         { return nand(a, a); }
static int gate_or(int a, int b)   { return nand(gate_not(a), gate_not(b)); }
static int gate_xor(int a, int b)  { int c = nand(a, b); return nand(nand(a, c), nand(b, c)); }

int equal4(const int *a, const int *b) {
    // TODO: XOR each bit pair, OR-reduce the differences into one bit, then invert
    // so 1 means "all bits matched". Use gate_xor, gate_or, gate_not only.
    (void)a; (void)b;             // remove once you use them
    (void)gate_or; (void)gate_xor;  // silences "unused" until you call them
    return 0;
}

static void to_bits(unsigned v, int *bits) { for (int i = 0; i < N; i++) bits[i] = (v >> i) & 1u; }

int main(void) {
    unsigned tests[][2] = { {5, 5}, {5, 7}, {0, 0}, {15, 14} };
    printf("   a  b | equal?\n");
    for (size_t t = 0; t < sizeof tests / sizeof *tests; t++) {
        int a[N], b[N];
        to_bits(tests[t][0], a);
        to_bits(tests[t][1], b);
        printf("  %2u %2u |   %d\n", tests[t][0], tests[t][1], equal4(a, b));
    }
    return 0;
}
