// Module 28 — Demo 4: Bitwise operators and the standard bit tricks
//
// & | ^ ~ << >> are how you manipulate individual bits. These are the building
// blocks of flags, masks, permissions (chmod!), hashing, and low-level protocols.
// Build & run with: make run4  — read alongside README.md §5.

#include <stdio.h>
#include <stdint.h>

static void print_bits8(uint8_t b) {
    for (int i = 7; i >= 0; i--) putchar((b >> i) & 1 ? '1' : '0');
}

// The four canonical single-bit operations on a register `x`, bit index `n`.
static uint8_t set_bit   (uint8_t x, int n) { return x |  (uint8_t)(1u << n); }
static uint8_t clear_bit (uint8_t x, int n) { return x & (uint8_t)~(1u << n); }
static uint8_t toggle_bit(uint8_t x, int n) { return x ^  (uint8_t)(1u << n); }
static int     test_bit  (uint8_t x, int n) { return (x >> n) & 1; }

int main(void) {
    printf("=== set / clear / toggle / test bit 3 ===\n");
    uint8_t x = 0;
    printf("  start    "); print_bits8(x); putchar('\n');
    x = set_bit(x, 3);    printf("  set 3    "); print_bits8(x); putchar('\n');
    x = set_bit(x, 6);    printf("  set 6    "); print_bits8(x); putchar('\n');
    x = toggle_bit(x, 3); printf("  toggle 3 "); print_bits8(x); putchar('\n');
    x = clear_bit(x, 6);  printf("  clear 6  "); print_bits8(x); putchar('\n');
    printf("  bit 3 set? %d\n", test_bit(x, 3));

    printf("\n=== Masks: extract the low nibble (bits 0-3) ===\n");
    uint8_t byte = 0xB7;             // 1011 0111
    uint8_t low = byte & 0x0F;        // keep low 4 bits
    uint8_t high = (byte >> 4) & 0x0F; // shift high nibble down
    printf("  0xB7 = "); print_bits8(byte);
    printf("  -> high nibble 0x%X, low nibble 0x%X\n", high, low);

    printf("\n=== Shifts multiply / divide by powers of two ===\n");
    printf("  5 << 1 = %d (x2),  5 << 3 = %d (x8),  40 >> 2 = %d (/4)\n",
           5 << 1, 5 << 3, 40 >> 2);

    printf("\n=== Three classic tricks ===\n");
    uint8_t v = 0x2C;  // 0010 1100
    // 1) power of two iff exactly one bit set: v & (v-1) == 0
    uint8_t p2 = 16;
    printf("  is %u a power of two? %s\n", p2, (p2 & (p2 - 1)) == 0 ? "yes" : "no");
    // 2) popcount: count set bits by clearing the lowest set bit each loop
    int count = 0;
    for (uint8_t t = v; t; t &= (uint8_t)(t - 1)) count++;
    printf("  popcount("); print_bits8(v); printf(") = %d set bits\n", count);
    // 3) XOR swap (no temp) — cute, rarely worth it, but shows XOR's self-inverse
    int a = 3, b = 9;
    a ^= b; b ^= a; a ^= b;
    printf("  XOR-swapped 3 and 9 -> a=%d b=%d\n", a, b);

    return 0;
}
