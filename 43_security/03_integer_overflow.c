// Module 43 — Demo 3: Integer overflow -> undersized allocation (EXPLAIN-AND-FIX)
//
// White-hat / educational. A size computed as n * size can WRAP past SIZE_MAX, so the
// allocation is far smaller than the caller intended — and the subsequent loop writes
// past it (a heap overflow). This demo shows the wraparound and the bug WITHOUT ever
// performing the unsafe write: the vulnerable path DETECTS the too-small buffer and
// refuses to write. Then the checked-multiply / calloc fixes. Build: make run3.
//
// Ties to Module 28 (unsigned wraparound is defined: it's arithmetic mod 2^N).
// Read alongside README.md §3.

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// VULNERABLE shape: trusts that count * elem fits in size_t. We compute the wrapped
// size, show it, and then — instead of writing past the buffer (which would be the
// real exploit) — we detect the mismatch and bail. The teaching point is the WRAP.
static int alloc_buffer_vulnerable(size_t count, size_t elem) {
    size_t bytes = count * elem;                 // BUG: can wrap around
    printf("  requested: %zu * %zu = %zu bytes (wrapped if tiny!)\n",
           count, elem, bytes);

    unsigned char *buf = malloc(bytes ? bytes : 1);
    if (!buf) { printf("  malloc failed\n"); return -1; }

    // What the real bug would do next: write `count * elem` logical bytes into `buf`,
    // which only holds `bytes`. We do NOT do that. We detect it and refuse, proving
    // the allocation is undersized.
    int undersized = (count != 0 && bytes / count != elem);  // overflow happened
    if (undersized) {
        printf("  -> allocation is UNDERSIZED; a real bug would now overflow the heap.\n");
        printf("     (demo refuses to write — no corruption performed)\n");
    } else {
        memset(buf, 0, bytes);
        printf("  -> size is consistent; wrote %zu bytes safely.\n", bytes);
    }
    free(buf);
    return undersized ? -1 : 0;
}

// FIXED #1: explicit overflow check before multiplying.
static int alloc_buffer_checked(size_t count, size_t elem) {
    if (elem != 0 && count > SIZE_MAX / elem) {
        printf("  refused: %zu * %zu would overflow size_t\n", count, elem);
        return -1;
    }
    size_t bytes = count * elem;
    unsigned char *buf = malloc(bytes ? bytes : 1);
    if (!buf) return -1;
    memset(buf, 0, bytes);
    printf("  ok: allocated and zeroed %zu bytes\n", bytes);
    free(buf);
    return 0;
}

// FIXED #2: let the library do the check. calloc(count, elem) returns NULL on overflow.
static int alloc_buffer_calloc(size_t count, size_t elem) {
    unsigned char *buf = calloc(count, elem);
    if (!buf) { printf("  calloc returned NULL (overflow or OOM) — handled safely\n"); return -1; }
    printf("  ok: calloc gave a correctly-sized, zeroed buffer\n");
    free(buf);
    return 0;
}

int main(void) {
    printf("=== Integer overflow in a size calculation ===\n\n");

    // Pick values whose product overflows size_t. On a 64-bit machine SIZE_MAX is
    // 2^64-1; (SIZE_MAX/2 + 1) * 4 wraps to a small number.
    size_t count = SIZE_MAX / 4 + 1;   // ~4.6e18
    size_t elem  = 8;                  // (count * 8) overflows 64-bit size_t

    printf("Vulnerable multiply (count=%zu, elem=%zu):\n", count, elem);
    alloc_buffer_vulnerable(count, elem);

    printf("\nFix #1 — explicit overflow check before *:\n");
    alloc_buffer_checked(count, elem);
    printf("  a legitimate request (count=16, elem=8):\n  ");
    alloc_buffer_checked(16, 8);

    printf("\nFix #2 — calloc() does the overflow check for you:\n");
    alloc_buffer_calloc(count, elem);
    printf("  a legitimate request (count=16, elem=8):\n  ");
    alloc_buffer_calloc(16, 8);

    printf("\nRule: never compute an allocation size with unchecked n*size.\n");
    return 0;
}
