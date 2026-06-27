// Module 29 — Demo 3: Binary addition — half adder -> full adder -> ripple carry
//
// Addition is the first piece of real arithmetic we can build from gates. We go:
//   half_adder  : adds two bits            -> (sum, carry)
//   full_adder  : adds two bits + carry-in -> (sum, carry-out)
//   add4 / add8 : chain N full adders, carry rippling from bit 0 upward
//
// Then the payoff from Module 28: SUBTRACTION is just ADDITION of the two's
// complement. a - b == a + (~b + 1). The same adder hardware does both.
// Build & run: make run3.  Read alongside README.md §3.
//
// Multi-bit values are arrays of int bits, index 0 = least-significant bit (LSB).

#include <stdio.h>

// ---- gates from NAND (local copy so the demo stands alone) -------------------
static int nand(int a, int b)      { return !(a && b); }
static int gate_not(int a)         { return nand(a, a); }
static int gate_and(int a, int b)  { return gate_not(nand(a, b)); }
static int gate_or(int a, int b)   { return nand(gate_not(a), gate_not(b)); }
static int gate_xor(int a, int b)  { int c = nand(a, b); return nand(nand(a, c), nand(b, c)); }

// ---- HALF ADDER --------------------------------------------------------------
// Adds two bits. sum = a XOR b (1 when they differ); carry = a AND b (1 only when
// both are 1, i.e. 1+1 = "10" in binary -> sum 0, carry 1).
static void half_adder(int a, int b, int *sum, int *carry) {
    *sum   = gate_xor(a, b);
    *carry = gate_and(a, b);
}

// ---- FULL ADDER --------------------------------------------------------------
// Adds three bits: a, b, and a carry-in cin. Two half adders plus an OR:
//   first half-add a+b, then half-add that sum with cin; carry out if either
//   half-add produced a carry.
static void full_adder(int a, int b, int cin, int *sum, int *cout) {
    int s1, c1, c2;
    half_adder(a, b, &s1, &c1);     // a + b
    half_adder(s1, cin, sum, &c2);  // (a+b) + cin
    *cout = gate_or(c1, c2);        // carry out from either stage
}

// ---- RIPPLE-CARRY ADDER ------------------------------------------------------
// Chain n full adders: bit i takes the carry-out of bit i-1 as its carry-in.
// Carry "ripples" from LSB to MSB, exactly like adding on paper. Returns the
// final carry-out (the overflow bit).
static int ripple_add(const int *a, const int *b, int *out, int n, int cin) {
    int carry = cin;
    for (int i = 0; i < n; i++) {
        full_adder(a[i], b[i], carry, &out[i], &carry);
    }
    return carry;  // carry out of the top bit
}

static int add4(const int *a, const int *b, int *out) { return ripple_add(a, b, out, 4, 0); }
static int add8(const int *a, const int *b, int *out) { return ripple_add(a, b, out, 8, 0); }

// ---- helpers: convert between int value and a bit array (LSB at index 0) ------
static void to_bits(unsigned value, int *bits, int n) {
    for (int i = 0; i < n; i++) bits[i] = (value >> i) & 1u;
}
static unsigned from_bits(const int *bits, int n) {
    unsigned v = 0;
    for (int i = 0; i < n; i++) v |= (unsigned)bits[i] << i;
    return v;
}
// Print bits MSB-first so they read like a written binary number.
static void print_bits(const int *bits, int n) {
    for (int i = n - 1; i >= 0; i--) putchar(bits[i] ? '1' : '0');
}

int main(void) {
    printf("=== Half adder (a + b) ===\n");
    printf("  a b | sum carry\n");
    for (int a = 0; a <= 1; a++)
        for (int b = 0; b <= 1; b++) {
            int s, c; half_adder(a, b, &s, &c);
            printf("  %d %d |  %d    %d\n", a, b, s, c);
        }

    printf("\n=== Full adder (a + b + carry-in) ===\n");
    printf("  a b cin | sum cout\n");
    for (int a = 0; a <= 1; a++)
        for (int b = 0; b <= 1; b++)
            for (int cin = 0; cin <= 1; cin++) {
                int s, c; full_adder(a, b, cin, &s, &c);
                printf("  %d %d  %d  |  %d    %d\n", a, b, cin, s, c);
            }

    printf("\n=== 4-bit ripple-carry add: 5 + 6 ===\n");
    int a4[4], b4[4], r4[4];
    to_bits(5, a4, 4); to_bits(6, b4, 4);
    int carry = add4(a4, b4, r4);
    printf("    "); print_bits(a4, 4); printf("  (%u)\n", from_bits(a4, 4));
    printf("  + "); print_bits(b4, 4); printf("  (%u)\n", from_bits(b4, 4));
    printf("  = "); print_bits(r4, 4);
    printf("  (%u)   carry-out=%d\n", from_bits(r4, 4), carry);

    printf("\n=== 4-bit overflow: 12 + 5 wraps (only 4 bits to hold it) ===\n");
    to_bits(12, a4, 4); to_bits(5, b4, 4);
    carry = add4(a4, b4, r4);
    printf("  12 + 5 = %u  carry-out=%d  (17 needs a 5th bit -> wraps to %u)\n",
           from_bits(r4, 4), carry, from_bits(r4, 4));

    printf("\n=== 8-bit ripple-carry add: 100 + 27 ===\n");
    int x8[8], y8[8], s8[8];
    to_bits(100, x8, 8); to_bits(27, y8, 8);
    int c8 = add8(x8, y8, s8);
    printf("  "); print_bits(x8, 8); printf(" + "); print_bits(y8, 8);
    printf(" = "); print_bits(s8, 8);
    printf("  (%u, carry=%d)\n", from_bits(s8, 8), c8);

    printf("\n=== Subtraction via two's complement: 9 - 4 (8-bit) ===\n");
    // a - b == a + (~b + 1). We invert b's bits and feed carry-in = 1, which adds
    // the +1 for free. Same ripple adder, no separate subtractor needed.
    int a8[8], b8[8], nb8[8], r8[8];
    to_bits(9, a8, 8);
    to_bits(4, b8, 8);
    for (int i = 0; i < 8; i++) nb8[i] = gate_not(b8[i]);  // ~b
    int cout = ripple_add(a8, nb8, r8, 8, 1);             // a + ~b + 1
    printf("       a = "); print_bits(a8, 8); printf("  (%u)\n", from_bits(a8, 8));
    printf("      ~b = "); print_bits(nb8, 8); printf("\n");
    printf("  a+~b+1 = "); print_bits(r8, 8);
    printf("  (%u)   (carry-out=%d discarded)\n", from_bits(r8, 8), cout);
    printf("  -> 9 - 4 = %u\n", from_bits(r8, 8));

    printf("\nOne ripple adder + bit-inversion = add AND subtract. This is exactly\n");
    printf("why two's complement (Module 28) is the representation hardware uses.\n");
    return 0;
}
