// SOLUTION 43.3 — Checked multiplication for an allocation size

#include <stdio.h>
#include <stdint.h>
#include <stddef.h>

static int alloc_size(size_t count, size_t elem, size_t *bytes) {
    // Guard BEFORE multiplying: if count > SIZE_MAX / elem the product won't fit.
    // (elem == 0 can't overflow; the product is 0.)
    if (elem != 0 && count > SIZE_MAX / elem) {
        *bytes = 0;
        return -1;            // refuse — caller must not allocate
    }
    *bytes = count * elem;    // now guaranteed not to wrap
    return 0;
}

int main(void) {
    struct { size_t count, elem; } cases[] = {
        { 16, 8 },                    // fine -> 128
        { 0, 8 },                     // fine -> 0
        { SIZE_MAX / 4 + 1, 8 },      // overflows on 64-bit -> must be refused
    };
    for (size_t i = 0; i < sizeof cases / sizeof *cases; i++) {
        size_t bytes = 0;
        int rc = alloc_size(cases[i].count, cases[i].elem, &bytes);
        if (rc == 0) printf("count=%zu elem=%zu -> %zu bytes (ok)\n",
                            cases[i].count, cases[i].elem, bytes);
        else         printf("count=%zu elem=%zu -> REFUSED (overflow)\n",
                            cases[i].count, cases[i].elem);
    }
    return 0;
}
