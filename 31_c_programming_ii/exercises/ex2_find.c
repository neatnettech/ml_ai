// Exercise 31.2 — A generic search with a PREDICATE function pointer
//
// Implement `find` so it returns the INDEX of the first element for which the
// predicate returns true (nonzero), or -1 if none match. The predicate is passed
// in as a function pointer, so the same `find` works for "first even", "first
// negative", or any rule the caller invents.
//
// Build & run:  make ex2     Reference: ../solutions/ex2_find.c

#include <stdio.h>

// Predicates: each takes one int and returns 1 (matches) or 0 (doesn't).
static int is_even(int x)     { return x % 2 == 0; }
static int is_negative(int x) { return x < 0; }

// TODO: implement find. Signature is fixed (do not change it).
//   - loop i from 0 to n-1
//   - if pred(arr[i]) is nonzero, return i
//   - if nothing matches, return -1
static int find(int *arr, int n, int (*pred)(int)) {
    (void)arr; (void)n; (void)pred;   // remove these once you use the parameters
    return -1;                         // TODO: replace with the real search
}

int main(void) {
    int xs[] = {7, 3, 8, -2, 5};
    int n = (int)(sizeof xs / sizeof xs[0]);

    printf("first even     at index %d  (expected 2)\n", find(xs, n, is_even));
    printf("first negative at index %d  (expected 3)\n", find(xs, n, is_negative));
    return 0;
}
