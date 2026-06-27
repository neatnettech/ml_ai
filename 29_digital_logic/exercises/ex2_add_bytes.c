// Exercise 29.2 — An 8-bit ripple-carry adder
//
// Implement `add8(a, b, out)` that adds two 8-bit numbers (arrays of int bits,
// index 0 = LSB) by chaining 8 full adders, the carry rippling from bit 0 upward.
// Return the final carry-out. Use the provided full_adder().
//
// Then `make ex2` should match the expected output in README.md §6.
// Solution in ../solutions/ex2_add_bytes.c.

#include <stdio.h>

#define N 8

static int nand(int a, int b)      { return !(a && b); }
static int gate_not(int a)         { return nand(a, a); }
static int gate_and(int a, int b)  { return gate_not(nand(a, b)); }
static int gate_or(int a, int b)   { return nand(gate_not(a), gate_not(b)); }
static int gate_xor(int a, int b)  { int c = nand(a, b); return nand(nand(a, c), nand(b, c)); }

static void full_adder(int a, int b, int cin, int *sum, int *cout) {
    int s1 = gate_xor(a, b);
    int c1 = gate_and(a, b);
    *sum   = gate_xor(s1, cin);
    int c2 = gate_and(s1, cin);
    *cout  = gate_or(c1, c2);
}

int add8(const int *a, const int *b, int *out) {
    // TODO: loop i from 0 to N-1, calling full_adder on a[i], b[i] and the running
    // carry, writing each sum bit into out[i]. Start carry at 0. Return final carry.
    (void)a; (void)b; (void)out;  // remove once you use them
    (void)full_adder;             // silences "unused" until you call it
    return 0;
}

static void to_bits(unsigned v, int *bits) { for (int i = 0; i < N; i++) bits[i] = (v >> i) & 1u; }
static unsigned from_bits(const int *bits)  { unsigned x = 0; for (int i = 0; i < N; i++) x |= (unsigned)bits[i] << i; return x; }
static void print_bits(const int *bits)     { for (int i = N - 1; i >= 0; i--) putchar(bits[i] ? '1' : '0'); }

int main(void) {
    unsigned tests[][2] = { {100, 27}, {200, 100}, {255, 1} };
    for (size_t t = 0; t < sizeof tests / sizeof *tests; t++) {
        int a[N], b[N], r[N];
        to_bits(tests[t][0], a);
        to_bits(tests[t][1], b);
        int carry = add8(a, b, r);
        printf("  "); print_bits(a); printf(" + "); print_bits(b);
        printf(" = "); print_bits(r);
        printf("  (%u + %u = %u, carry=%d)\n",
               tests[t][0], tests[t][1], from_bits(r), carry);
    }
    return 0;
}
