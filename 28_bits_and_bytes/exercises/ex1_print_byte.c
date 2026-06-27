// Exercise 28.1 — Print a byte in binary
//
// Implement `print_byte` so it prints the 8 bits of `b`, most-significant bit first
// (so 65 prints as 01000001). Then `make ex1` should match the expected output in
// README.md §6. Solution in ../solutions/ex1_print_byte.c.

#include <stdio.h>
#include <stdint.h>

void print_byte(uint8_t b) {
    // TODO: print the 8 bits of b, high bit (bit 7) first, no spaces, then a newline.
    // Hint: loop i from 7 down to 0, print (b >> i) & 1.
    (void)b;  // remove this line once you use b
}

int main(void) {
    uint8_t samples[] = {0, 1, 65, 128, 255};
    for (size_t i = 0; i < sizeof samples / sizeof *samples; i++) {
        printf("%3u = ", samples[i]);
        print_byte(samples[i]);
    }
    return 0;
}
