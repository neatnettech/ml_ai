// Exercise 43.2 — Constant-time equality
//
// Implement `ct_equal(a, b, n)` returning 1 if the two n-byte buffers are equal, 0
// otherwise — in CONSTANT TIME, i.e. the running time must NOT depend on where (or
// whether) the buffers first differ. A naive loop that `return 0`s on the first
// mismatch leaks, via timing, how many leading bytes matched — enough to recover a
// secret tag byte by byte (see Demo 4 / Module 18).
//
// TODO: implement ct_equal without early-exit branches inside the loop.
// Hint: OR-accumulate (a[i] ^ b[i]) over every byte; compare the accumulator to 0
// once at the end. In your README answer, say WHY this defeats the timing attack.
//
// Solution: ../solutions/ex2_constant_time_eq.c

#include <stdio.h>
#include <stddef.h>

static int ct_equal(const unsigned char *a, const unsigned char *b, size_t n) {
    // TODO: replace this early-exit version with a constant-time comparison.
    for (size_t i = 0; i < n; i++) {
        if (a[i] != b[i]) return 0;   // <- leaks timing; remove the early exit
    }
    return 1;
}

int main(void) {
    unsigned char tag[]    = { 0xa1, 0xb2, 0xc3, 0xd4 };
    unsigned char same[]   = { 0xa1, 0xb2, 0xc3, 0xd4 };
    unsigned char diff1[]  = { 0x00, 0xb2, 0xc3, 0xd4 };  // differs at byte 0
    unsigned char diff4[]  = { 0xa1, 0xb2, 0xc3, 0x00 };  // differs at byte 3

    printf("ct_equal(tag, same)  = %d  (expect 1)\n", ct_equal(tag, same, 4));
    printf("ct_equal(tag, diff1) = %d  (expect 0)\n", ct_equal(tag, diff1, 4));
    printf("ct_equal(tag, diff4) = %d  (expect 0)\n", ct_equal(tag, diff4, 4));
    return 0;
}
