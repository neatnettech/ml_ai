// Exercise 38.1 — Quicksort's partition step
//
// Quicksort's whole engine is `partition`: pick a pivot, rearrange the range so
// everything smaller sits left of the pivot and everything larger sits right,
// then return the pivot's final index. Implement it (and the partition is the
// part that matters); the recursion driving it is given. Then `make ex1` should
// match `make sol1`. Solution in ../solutions/ex1_quicksort.c.

#include <stdio.h>
#include <stddef.h>

static void swap_int(int *a, int *b) { int t = *a; *a = *b; *b = t; }

// Partition a[lo..hi) using the LAST element a[hi-1] as the pivot (Lomuto scheme).
// Move every element < pivot to the left part, place the pivot after them, and
// return the pivot's final index.
static size_t partition(int *a, size_t lo, size_t hi) {
    // TODO: implement Lomuto partition.
    //  1. pivot = a[hi - 1]
    //  2. keep a `store` index starting at lo
    //  3. for i in [lo, hi-1): if a[i] < pivot, swap a[i] with a[store], store++
    //  4. swap a[store] with a[hi-1] to drop the pivot into place
    //  5. return store
    (void)a; (void)lo; (void)swap_int;  // remove these once you use them
    return hi - 1;                // placeholder — replace with the real result
}

static void quicksort_rec(int *a, size_t lo, size_t hi) {
    if (hi - lo < 2) return;
    size_t p = partition(a, lo, hi);
    quicksort_rec(a, lo, p);
    quicksort_rec(a, p + 1, hi);
}

static int is_sorted(const int *a, size_t n) {
    for (size_t i = 1; i < n; i++) if (a[i - 1] > a[i]) return 0;
    return 1;
}

int main(void) {
    int a[] = {9, 3, 7, 1, 8, 2, 5, 4, 6, 0, 5, 3};
    size_t n = sizeof a / sizeof *a;

    printf("before: ");
    for (size_t i = 0; i < n; i++) printf("%d ", a[i]);
    printf("\n");

    quicksort_rec(a, 0, n);

    printf("after:  ");
    for (size_t i = 0; i < n; i++) printf("%d ", a[i]);
    printf("\nsorted? %s\n", is_sorted(a, n) ? "YES" : "NO");
    return 0;
}
