// Module 28 — Demo 3: IEEE-754 floating point, taken apart
//
// A float is not a "decimal number" — it's sign x 1.mantissa x 2^exponent, packed
// into 32 bits (1 sign + 8 exponent + 23 mantissa). This program decomposes a float
// into those fields and shows why 0.1 + 0.2 != 0.3. Build & run with: make run3
// Read alongside README.md §4.

#include <stdio.h>
#include <stdint.h>
#include <string.h>

// Reinterpret the 32 bits of a float as a uint32 WITHOUT changing them.
// (A union or memcpy is the correct way; a pointer cast would break strict aliasing.)
static uint32_t float_bits(float f) {
    uint32_t u;
    memcpy(&u, &f, sizeof u);
    return u;
}

static void decompose(float f) {
    uint32_t u = float_bits(f);
    uint32_t sign = (u >> 31) & 0x1;
    uint32_t exp  = (u >> 23) & 0xFF;   // 8 bits, biased by 127
    uint32_t mant =  u        & 0x7FFFFF; // 23 bits

    printf("  %-12g  bits: ", (double)f);
    for (int i = 31; i >= 0; i--) {
        putchar((u >> i) & 1 ? '1' : '0');
        if (i == 31 || i == 23) putchar(' ');  // separate sign | exp | mantissa
    }
    printf("\n               sign=%u exp=%u (unbiased %d) mantissa=0x%06X\n",
           sign, exp, (int)exp - 127, mant);
}

int main(void) {
    printf("=== Layout: [sign][8-bit exponent][23-bit mantissa] ===\n");
    decompose(0.0f);
    decompose(1.0f);
    decompose(-2.0f);
    decompose(0.5f);
    decompose(0.1f);   // NOT representable exactly in binary

    printf("\n=== Special values ===\n");
    float inf = 1.0f / 0.0f;
    float ninf = -1.0f / 0.0f;
    float nan = 0.0f / 0.0f;
    decompose(inf);    // exp all 1s, mantissa 0
    decompose(nan);    // exp all 1s, mantissa != 0
    printf("  inf > 1e30? %s   nan == nan? %s  (NaN is never equal to anything)\n",
           inf > 1e30f ? "yes" : "no", nan == nan ? "yes" : "no");
    (void)ninf;

    printf("\n=== The classic: 0.1 + 0.2 ===\n");
    double r = 0.1 + 0.2;
    printf("  0.1 + 0.2 = %.17f\n", r);
    printf("  == 0.3?   %s   (rounding error: 0.1 and 0.2 aren't exact in binary)\n",
           r == 0.3 ? "yes" : "no");

    return 0;
}
