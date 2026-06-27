// SOLUTION 28.1 — Print a byte in binary

#include <stdio.h>
#include <stdint.h>

void print_byte(uint8_t b) {
    for (int i = 7; i >= 0; i--) {
        putchar((b >> i) & 1 ? '1' : '0');
    }
    putchar('\n');
}

int main(void) {
    uint8_t samples[] = {0, 1, 65, 128, 255};
    for (size_t i = 0; i < sizeof samples / sizeof *samples; i++) {
        printf("%3u = ", samples[i]);
        print_byte(samples[i]);
    }
    return 0;
}
