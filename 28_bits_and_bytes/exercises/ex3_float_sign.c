// Exercise 28.3 — Read a float's sign bit without comparing to 0.0
//
// Implement `is_negative` using ONLY the bits of the float (no `f < 0`), so it also
// reports the sign of -0.0 correctly (which `f < 0` cannot). Run with `make ex3`.
// Hint: copy the bits into a uint32_t (memcpy), then look at bit 31.

#include <stdio.h>
#include <stdint.h>
#include <string.h>

int is_negative(float f) {
    // TODO: return 1 if the sign bit (bit 31) is set, else 0 — using the raw bits.
    // Hint: uint32_t u; memcpy(&u, &f, sizeof u); return (u >> 31) & 1;
    (void)f;
    return -1;  // replace
}

int main(void) {
    float samples[] = {3.5f, -3.5f, 0.0f, -0.0f, 1e30f, -1e-30f};
    for (size_t i = 0; i < sizeof samples / sizeof *samples; i++) {
        printf("is_negative(%-10g) = %d\n", (double)samples[i], is_negative(samples[i]));
    }
    // Note: is_negative(-0.0) should be 1, even though (-0.0 < 0) is false!
    return 0;
}
