// Exercise 43.3 — Checked multiplication for an allocation size
//
// `alloc_size` computes how many bytes to allocate for `count` elements of `elem`
// bytes each. Done naively (count * elem) the product can WRAP past SIZE_MAX, yielding
// a tiny size and — once the caller writes count*elem real bytes — a heap overflow.
//
// TODO: make alloc_size detect the overflow and fail safely. On overflow, set *bytes
// to 0 and return -1; otherwise set *bytes to the product and return 0.
// Hint: before multiplying, check `elem != 0 && count > SIZE_MAX / elem`.
// (calloc() does exactly this check internally — but here you implement it.)
//
// Solution: ../solutions/ex3_checked_alloc_size.c

#include <stdio.h>
#include <stdint.h>
#include <stddef.h>

static int alloc_size(size_t count, size_t elem, size_t *bytes) {
    // TODO: add the overflow guard. Right now it multiplies blindly.
    *bytes = count * elem;   // <- can wrap; replace with a checked version
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
