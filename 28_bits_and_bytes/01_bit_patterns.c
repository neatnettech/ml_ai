// Module 28 — Demo 1: Bit patterns, bytes, and endianness
//
// Everything in a computer is bytes; a byte is 8 bits. This program shows how to
// SEE those bits for any value, how big each C type is, and how multi-byte values
// are laid out in memory (endianness). Build & run with: make run1
//
// Read top to bottom alongside README.md §1–§2.

#include <stdio.h>
#include <stdint.h>
#include <string.h>

// Print the raw bits of ANY object, byte by byte, most-significant byte first.
// We take a void* + size so it works for an int, a float, a struct — anything.
static void print_bits(const void *obj, size_t nbytes) {
    // Treat the object as an array of bytes. `unsigned char` is the one type the C
    // standard guarantees you may use to inspect the bytes of any other object.
    const unsigned char *bytes = (const unsigned char *)obj;
    // Print high byte to low byte so the output reads like a written binary number.
    for (size_t i = nbytes; i-- > 0;) {
        for (int bit = 7; bit >= 0; bit--) {
            putchar((bytes[i] >> bit) & 1 ? '1' : '0');
        }
        putchar(' ');
    }
    putchar('\n');
}

int main(void) {
    printf("=== Sizes of C types (bytes) ===\n");
    printf("  char        %zu\n", sizeof(char));
    printf("  short       %zu\n", sizeof(short));
    printf("  int         %zu\n", sizeof(int));
    printf("  long        %zu\n", sizeof(long));
    printf("  float       %zu\n", sizeof(float));
    printf("  double      %zu\n", sizeof(double));
    printf("  void *      %zu\n", sizeof(void *));

    printf("\n=== One byte: the number 65 ('A') ===\n");
    unsigned char c = 65;
    printf("  decimal %u, hex 0x%02X, char '%c', bits ", c, c, c);
    print_bits(&c, sizeof c);

    printf("\n=== A 32-bit int: 0x0A0B0C0D ===\n");
    uint32_t n = 0x0A0B0C0D;
    printf("  value as we wrote it (high->low byte): ");
    print_bits(&n, sizeof n);
    printf("  the SAME int, byte-by-byte in MEMORY order (low address first):\n  ");
    const unsigned char *p = (const unsigned char *)&n;
    for (size_t i = 0; i < sizeof n; i++) printf("0x%02X ", p[i]);
    putchar('\n');
    // On a little-endian machine (x86-64, Apple Silicon) the least-significant byte
    // 0x0D sits at the lowest address — the bytes come out 0D 0C 0B 0A.
    printf("  -> first byte in memory is 0x%02X => this machine is %s-endian\n",
           p[0], p[0] == 0x0D ? "LITTLE" : "BIG");

    return 0;
}
