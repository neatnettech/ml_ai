// SOLUTION 38.1 — Quicksort's partition step (Lomuto scheme)

#include <stdio.h>
#include <stddef.h>

static void swap_int(int *a, int *b) { int t = *a; *a = *b; *b = t; }

static size_t partition(int *a, size_t lo, size_t hi) {
    int pivot = a[hi - 1];
    size_t store = lo;
    for (size_t i = lo; i < hi - 1; i++) {
        if (a[i] < pivot) {
            swap_int(&a[i], &a[store]);
            store++;
        }
    }
    swap_int(&a[store], &a[hi - 1]);
    return store;
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
