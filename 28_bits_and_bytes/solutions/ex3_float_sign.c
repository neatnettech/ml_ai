// SOLUTION 28.3 — Read a float's sign bit from the raw bits

#include <stdio.h>
#include <stdint.h>
#include <string.h>

int is_negative(float f) {
    uint32_t u;
    memcpy(&u, &f, sizeof u);
    return (int)((u >> 31) & 1);
}

int main(void) {
    float samples[] = {3.5f, -3.5f, 0.0f, -0.0f, 1e30f, -1e-30f};
    for (size_t i = 0; i < sizeof samples / sizeof *samples; i++) {
        printf("is_negative(%-10g) = %d\n", (double)samples[i], is_negative(samples[i]));
    }
    return 0;
}
