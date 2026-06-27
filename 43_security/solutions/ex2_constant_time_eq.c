// SOLUTION 43.2 — Constant-time equality
//
// Why this is constant-time: the loop ALWAYS visits all n bytes (no early return),
// and the only data-dependent operation is an OR into an accumulator, which takes the
// same time regardless of the values. The single branch happens once, after the loop,
// on the accumulated result — so the running time depends only on n, never on the
// CONTENT or on where the buffers differ. An attacker timing the comparison learns
// nothing about how many leading bytes were correct, defeating byte-by-byte recovery.

#include <stdio.h>
#include <stddef.h>

static int ct_equal(const unsigned char *a, const unsigned char *b, size_t n) {
    unsigned char diff = 0;
    for (size_t i = 0; i < n; i++) {
        diff |= (unsigned char)(a[i] ^ b[i]);   // 0 stays 0 only if all bytes match
    }
    return diff == 0;                            // single branch, after touching all
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
