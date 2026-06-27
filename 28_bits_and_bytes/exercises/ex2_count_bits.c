// Exercise 28.2 — Count the set bits (popcount)
//
// Implement `count_bits` to return how many 1-bits are in `x` (a 32-bit value).
// Run with `make ex2`; expected output is in README.md §6.
// Bonus: do it in O(number-of-set-bits) using the `x & (x-1)` trick from demo 4.

#include <stdio.h>
#include <stdint.h>

int count_bits(uint32_t x) {
    // TODO: return the number of bits set to 1 in x.
    // Hint A (simple): loop 32 times, add (x >> i) & 1.
    // Hint B (clever): while (x) { x &= x - 1; count++; } — clears lowest set bit.
    (void)x;
    return -1;  // replace
}

int main(void) {
    uint32_t samples[] = {0u, 1u, 0xFFu, 0xFFFFFFFFu, 0xB4u};
    for (size_t i = 0; i < sizeof samples / sizeof *samples; i++) {
        printf("count_bits(0x%08X) = %d\n", samples[i], count_bits(samples[i]));
    }
    return 0;
}
