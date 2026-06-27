// Module 38 — Demo 1: Sorting & asymptotics
//
// Three classic sorts on growing input sizes, timed, so the O(n^2) vs O(n log n)
// gap is something you SEE rather than take on faith. Insertion sort is quadratic;
// merge sort and quicksort are n log n. As n doubles, watch insertion's time roughly
// quadruple while the others a bit more than double. Build & run with: make run1
//
// Read top to bottom alongside README.md §1.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// ---- insertion sort: O(n^2) ------------------------------------------------
// Grow a sorted prefix one element at a time, shifting bigger elements right.
static void insertion_sort(int *a, size_t n) {
    for (size_t i = 1; i < n; i++) {
        int key = a[i];
        size_t j = i;
        while (j > 0 && a[j - 1] > key) {
            a[j] = a[j - 1];
            j--;
        }
        a[j] = key;
    }
}

// ---- merge sort: O(n log n) ------------------------------------------------
// Split in half, sort each half, merge the two sorted halves. `tmp` is scratch.
static void merge(int *a, int *tmp, size_t lo, size_t mid, size_t hi) {
    size_t i = lo, j = mid, k = lo;
    while (i < mid && j < hi) tmp[k++] = (a[i] <= a[j]) ? a[i++] : a[j++];
    while (i < mid) tmp[k++] = a[i++];
    while (j < hi) tmp[k++] = a[j++];
    memcpy(a + lo, tmp + lo, (hi - lo) * sizeof(int));
}

static void merge_sort_rec(int *a, int *tmp, size_t lo, size_t hi) {
    if (hi - lo < 2) return;            // 0 or 1 element is already sorted
    size_t mid = lo + (hi - lo) / 2;
    merge_sort_rec(a, tmp, lo, mid);
    merge_sort_rec(a, tmp, mid, hi);
    merge(a, tmp, lo, mid, hi);
}

static void merge_sort(int *a, size_t n) {
    int *tmp = malloc(n * sizeof(int));
    if (!tmp) { perror("malloc"); exit(1); }
    merge_sort_rec(a, tmp, 0, n);
    free(tmp);
}

// ---- quicksort: O(n log n) average -----------------------------------------
// Partition around a pivot (median-of-three to avoid the sorted-input worst
// case), then recurse into each side.
static void swap_int(int *x, int *y) { int t = *x; *x = *y; *y = t; }

static size_t partition(int *a, size_t lo, size_t hi) {
    size_t mid = lo + (hi - lo) / 2;            // median-of-three pivot choice
    if (a[mid] < a[lo]) swap_int(&a[mid], &a[lo]);
    if (a[hi]  < a[lo]) swap_int(&a[hi],  &a[lo]);
    if (a[hi]  < a[mid]) swap_int(&a[hi], &a[mid]);
    int pivot = a[mid];
    swap_int(&a[mid], &a[hi - 1]);              // park pivot at hi-1
    size_t store = lo;
    for (size_t i = lo; i < hi - 1; i++) {
        if (a[i] < pivot) swap_int(&a[i], &a[store++]);
    }
    swap_int(&a[store], &a[hi - 1]);            // restore pivot to its slot
    return store;
}

static void quicksort_rec(int *a, size_t lo, size_t hi) {
    while (hi - lo > 1) {
        size_t p = partition(a, lo, hi);
        if (p - lo < hi - (p + 1)) {            // recurse into smaller side first
            quicksort_rec(a, lo, p);
            lo = p + 1;
        } else {
            quicksort_rec(a, p + 1, hi);
            hi = p;
        }
    }
}

static void quicksort(int *a, size_t n) { if (n > 1) quicksort_rec(a, 0, n); }

// ---- helpers ---------------------------------------------------------------
static int is_sorted(const int *a, size_t n) {
    for (size_t i = 1; i < n; i++) if (a[i - 1] > a[i]) return 0;
    return 1;
}

// A fixed, reproducible pseudo-random fill (no rand() seeding surprises).
static void fill_random(int *a, size_t n, unsigned *state) {
    for (size_t i = 0; i < n; i++) {
        *state = *state * 1103515245u + 12345u;   // classic LCG
        a[i] = (int)((*state >> 16) & 0x7FFF);
    }
}

// Time one sort over `n` ints. Returns milliseconds. We checksum the result and
// feed it to a volatile sink so the optimizer cannot delete the work.
static volatile long g_sink;
static double time_sort(void (*sort)(int *, size_t), const int *src, size_t n) {
    int *a = malloc(n * sizeof(int));
    if (!a) { perror("malloc"); exit(1); }
    memcpy(a, src, n * sizeof(int));
    clock_t t0 = clock();
    sort(a, n);
    clock_t t1 = clock();
    if (!is_sorted(a, n)) { fprintf(stderr, "BUG: not sorted!\n"); exit(1); }
    long sum = 0;
    for (size_t i = 0; i < n; i++) sum += a[i];   // touch the output
    g_sink = sum;
    free(a);
    return 1000.0 * (double)(t1 - t0) / CLOCKS_PER_SEC;
}

int main(void) {
    printf("=== Sorting: timing the asymptotic gap ===\n");
    printf("Each row sorts the SAME random array three ways. Watch how insertion\n");
    printf("sort (O(n^2)) blows up as n grows, while merge/quick (O(n log n)) crawl.\n\n");
    printf("%10s | %12s | %12s | %12s\n", "n", "insertion", "merge", "quick");
    printf("-----------+--------------+--------------+--------------\n");

    size_t sizes[] = {1000, 2000, 4000, 8000, 16000, 32000};
    for (size_t s = 0; s < sizeof sizes / sizeof *sizes; s++) {
        size_t n = sizes[s];
        unsigned state = 1u;                 // same seed => same array each row
        int *src = malloc(n * sizeof(int));
        if (!src) { perror("malloc"); exit(1); }
        fill_random(src, n, &state);

        double t_ins  = time_sort(insertion_sort, src, n);
        double t_mrg  = time_sort(merge_sort,     src, n);
        double t_qck  = time_sort(quicksort,      src, n);

        printf("%10zu | %10.2f ms | %10.2f ms | %10.2f ms\n",
               n, t_ins, t_mrg, t_qck);
        free(src);
    }

    printf("\nNote how doubling n ~4x's insertion's time but only ~2x's the others:\n");
    printf("that factor IS the difference between n^2 and n log n.\n");
    return 0;
}
