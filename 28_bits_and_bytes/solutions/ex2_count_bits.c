// SOLUTION 28.2 — Count the set bits (popcount), O(set bits) via x & (x-1)

#include <stdio.h>
#include <stdint.h>

int count_bits(uint32_t x) {
    int count = 0;
    while (x) {
        x &= x - 1;  // clears the lowest set bit
        count++;
    }
    return count;
}

int main(void) {
    uint32_t samples[] = {0u, 1u, 0xFFu, 0xFFFFFFFFu, 0xB4u};
    for (size_t i = 0; i < sizeof samples / sizeof *samples; i++) {
        printf("count_bits(0x%08X) = %d\n", samples[i], count_bits(samples[i]));
    }
    return 0;
}
