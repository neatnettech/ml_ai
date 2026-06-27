// SOLUTION 29.3 — An equality comparator from gates

#include <stdio.h>

#define N 4

static int nand(int a, int b)      { return !(a && b); }
static int gate_not(int a)         { return nand(a, a); }
static int gate_or(int a, int b)   { return nand(gate_not(a), gate_not(b)); }
static int gate_xor(int a, int b)  { int c = nand(a, b); return nand(nand(a, c), nand(b, c)); }

int equal4(const int *a, const int *b) {
    int diff = 0;  // OR-reduce of all bit differences
    for (int i = 0; i < N; i++) {
        diff = gate_or(diff, gate_xor(a[i], b[i]));
    }
    return gate_not(diff);  // equal iff no bit differed
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
