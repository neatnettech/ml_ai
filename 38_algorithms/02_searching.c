// Module 38 — Demo 2: Linear vs binary search
//
// Linear search scans every element: O(n). Binary search halves the range each
// step: O(log n) — but it REQUIRES sorted input. We count comparisons so the gap
// is concrete, and show what binary search returns when you feed it unsorted data.
// Build & run with: make run2
//
// Read top to bottom alongside README.md §2.

#include <stdio.h>
#include <stddef.h>

// Linear search: walk left to right until we find target. Counts each compare.
static long linear_search(const int *a, size_t n, int target, long *cmps) {
    for (size_t i = 0; i < n; i++) {
        (*cmps)++;
        if (a[i] == target) return (long)i;
    }
    return -1;
}

// Binary search: keep a [lo,hi) window, probe the middle, throw away half.
// Correct ONLY if `a` is sorted ascending.
static long binary_search(const int *a, size_t n, int target, long *cmps) {
    size_t lo = 0, hi = n;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        (*cmps)++;
        if (a[mid] == target) return (long)mid;
        if (a[mid] < target) lo = mid + 1;
        else hi = mid;
    }
    return -1;
}

int main(void) {
    // A sorted array of 1..n so binary search is valid.
    enum { N = 1000 };
    int sorted[N];
    for (int i = 0; i < N; i++) sorted[i] = i + 1;     // 1..1000

    printf("=== Linear vs binary search on a sorted array of %d ===\n\n", N);
    printf("%8s | %14s | %14s\n", "target", "linear cmps", "binary cmps");
    printf("---------+----------------+----------------\n");

    int targets[] = {1, 250, 500, 750, 1000, 1234 /* absent */};
    for (size_t t = 0; t < sizeof targets / sizeof *targets; t++) {
        long lc = 0, bc = 0;
        long li = linear_search(sorted, N, targets[t], &lc);
        long bi = binary_search(sorted, N, targets[t], &bc);
        if (li != bi) { fprintf(stderr, "BUG: searches disagree!\n"); return 1; }
        printf("%8d | %14ld | %14ld%s\n",
               targets[t], lc, bc, (bi < 0) ? "   (not found)" : "");
    }

    printf("\nBinary never exceeds ~ceil(log2(%d)) = 10 comparisons; linear can\n", N);
    printf("hit %d. That's the O(log n) vs O(n) difference.\n\n", N);

    // Why sorted input is mandatory: run binary search on UNSORTED data.
    printf("=== Binary search needs sorted input ===\n");
    int unsorted[] = {9, 3, 7, 1, 8, 2, 5, 4, 6, 0};
    size_t m = sizeof unsorted / sizeof *unsorted;
    int needle = 8;
    long uc = 0;
    long ui = binary_search(unsorted, m, needle, &uc);
    printf("array (unsorted): ");
    for (size_t i = 0; i < m; i++) printf("%d ", unsorted[i]);
    printf("\nbinary_search for %d => index %ld  (value 8 IS present at index 4,\n",
           needle, ui);
    printf("but binary search misses it because the input is not sorted).\n");
    return 0;
}
