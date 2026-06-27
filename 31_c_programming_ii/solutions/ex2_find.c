// SOLUTION 31.2 — generic find() with a predicate function pointer

#include <stdio.h>

static int is_even(int x)     { return x % 2 == 0; }
static int is_negative(int x) { return x < 0; }

static int find(int *arr, int n, int (*pred)(int)) {
    for (int i = 0; i < n; i++) {
        if (pred(arr[i])) return i;   // first match wins
    }
    return -1;                        // no element satisfied the predicate
}

int main(void) {
    int xs[] = {7, 3, 8, -2, 5};
    int n = (int)(sizeof xs / sizeof xs[0]);

    printf("first even     at index %d  (expected 2)\n", find(xs, n, is_even));
    printf("first negative at index %d  (expected 3)\n", find(xs, n, is_negative));

    // No match case:
    int odds[] = {1, 3, 5};
    printf("first even in {1,3,5} = %d  (expected -1)\n",
           find(odds, 3, is_even));
    return 0;
}
