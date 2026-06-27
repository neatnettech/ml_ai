// Module 28 — Demo 2: Signed integers and two's complement
//
// How does one pattern of bits mean -1? Two's complement: the top bit has NEGATIVE
// weight. This program shows signed vs unsigned reinterpretation, negation as
// "flip the bits and add 1", and what overflow actually looks like in the bits.
// Build & run with: make run2  — read alongside README.md §3.

#include <stdio.h>
#include <stdint.h>
#include <limits.h>

static void print_bits8(uint8_t b) {
    for (int i = 7; i >= 0; i--) putchar((b >> i) & 1 ? '1' : '0');
}

int main(void) {
    printf("=== One byte, read two ways ===\n");
    printf("  bits      unsigned   signed (two's complement)\n");
    int probes[] = {0, 1, 127, 128, 200, 255};
    for (size_t i = 0; i < sizeof probes / sizeof *probes; i++) {
        uint8_t u = (uint8_t)probes[i];
        int8_t s = (int8_t)u;  // same 8 bits, reinterpreted as signed
        printf("  ");
        print_bits8(u);
        printf("   %3u        %4d\n", u, s);
    }
    // 10000000 is 128 unsigned but -128 signed: the top bit's weight flips sign.

    printf("\n=== Negation = flip bits + 1 ===\n");
    int8_t x = 5;
    int8_t neg = (int8_t)(~(uint8_t)x + 1);  // do the math in unsigned to avoid UB
    printf("   5 = "); print_bits8((uint8_t)x);   printf("\n");
    printf("  ~5 = "); print_bits8((uint8_t)~(uint8_t)x); printf("  (flip)\n");
    printf("  +1 = "); print_bits8((uint8_t)neg); printf("  = %d\n", neg);

    printf("\n=== Overflow wraps around the ring ===\n");
    int8_t max = INT8_MAX;  // 127
    printf("  INT8_MAX = %d, bits ", max); print_bits8((uint8_t)max); putchar('\n');
    int8_t over = (int8_t)((uint8_t)max + 1);  // wrap in unsigned, then view signed
    printf("  +1 wraps to %d, bits ", over); print_bits8((uint8_t)over); putchar('\n');
    // 127 -> -128: the values live on a wheel, not a line. Signed overflow on the
    // actual `int8_t + 1` would be Undefined Behavior — see Module 31. We compute in
    // unsigned (defined to wrap) and reinterpret, which is the safe way to show it.

    printf("\n=== Why this matters ===\n");
    printf("  unsigned subtraction underflows to a huge number:\n");
    unsigned a = 3, b = 5;
    printf("  3u - 5u = %u  (NOT -2: unsigned can't be negative)\n", a - b);

    return 0;
}
