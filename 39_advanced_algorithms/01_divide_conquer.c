// Module 39 — Demo 1: Divide & Conquer — counting inversions in O(n log n)
//
// An *inversion* is a pair (i, j) with i < j but a[i] > a[j] — i.e. two elements
// out of order. The count of inversions measures "how unsorted" an array is (it is
// the number of swaps bubble sort would do). The naive way checks all C(n,2) pairs:
// O(n^2). The clever way piggybacks on merge sort: when we merge two sorted halves
// and pull an element from the RIGHT half ahead of `remaining` elements still in the
// LEFT half, every one of those left elements forms an inversion with it. So we count
// them for free during the merge, giving O(n log n).
//
// This demo runs both methods on the same array, checks they agree, and times them on
// a large random array to show the asymptotic win. Build & run with: make run1
//
// Read alongside README.md §1.

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// --- Naive O(n^2): just count every out-of-order pair. -----------------------------
static long long inversions_naive(const int *a, int n) {
    long long count = 0;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            if (a[i] > a[j]) count++;
    return count;
}

// --- Merge step: merge a[lo..mid) and a[mid..hi) (both sorted) into tmp, counting
//     inversions, then copy back. Returns inversions found during this merge. --------
static long long merge_count(int *a, int *tmp, int lo, int mid, int hi) {
    long long count = 0;
    int i = lo, j = mid, k = lo;
    while (i < mid && j < hi) {
        if (a[i] <= a[j]) {
            tmp[k++] = a[i++];
        } else {
            // a[j] is smaller than a[i], so it is smaller than ALL of a[i..mid):
            // that is (mid - i) inversions in one shot.
            tmp[k++] = a[j++];
            count += (mid - i);
        }
    }
    while (i < mid) tmp[k++] = a[i++];
    while (j < hi)  tmp[k++] = a[j++];
    for (int t = lo; t < hi; t++) a[t] = tmp[t];
    return count;
}

// --- Divide & conquer: sort each half, count inversions in each, add the cross ones. -
static long long inversions_dc(int *a, int *tmp, int lo, int hi) {
    if (hi - lo <= 1) return 0;           // 0 or 1 element: already sorted, no inversions
    int mid = lo + (hi - lo) / 2;
    long long count = inversions_dc(a, tmp, lo, mid);
    count += inversions_dc(a, tmp, mid, hi);
    count += merge_count(a, tmp, lo, mid, hi);
    return count;
}

static double seconds_since(clock_t start) {
    return (double)(clock() - start) / CLOCKS_PER_SEC;
}

int main(void) {
    printf("=== Counting inversions: naive O(n^2) vs divide & conquer O(n log n) ===\n\n");

    // 1) Small worked example so the count is checkable by hand.
    int demo[] = {2, 4, 1, 3, 5};
    int n = (int)(sizeof demo / sizeof *demo);
    printf("  array: ");
    for (int i = 0; i < n; i++) printf("%d ", demo[i]);
    printf("\n  inversions (pairs out of order): (2,1) (4,1) (4,3)\n");

    int *copy = malloc((size_t)n * sizeof *copy);
    int *tmp  = malloc((size_t)n * sizeof *tmp);
    for (int i = 0; i < n; i++) copy[i] = demo[i];
    long long naive = inversions_naive(demo, n);
    long long dc    = inversions_dc(copy, tmp, 0, n);
    printf("  naive = %lld, divide&conquer = %lld  -> %s\n\n",
           naive, dc, naive == dc ? "AGREE" : "DISAGREE");
    free(copy);
    free(tmp);

    // 2) Big random array: show the asymptotic gap in wall-clock time.
    int big_n = 20000;
    srand(12345);
    int *big   = malloc((size_t)big_n * sizeof *big);
    int *bigc  = malloc((size_t)big_n * sizeof *bigc);
    int *bigt  = malloc((size_t)big_n * sizeof *bigt);
    for (int i = 0; i < big_n; i++) big[i] = rand();
    for (int i = 0; i < big_n; i++) bigc[i] = big[i];

    clock_t t0 = clock();
    long long bn = inversions_naive(big, big_n);
    double naive_s = seconds_since(t0);

    t0 = clock();
    long long bd = inversions_dc(bigc, bigt, 0, big_n);   // sorts bigc in place
    double dc_s = seconds_since(t0);

    printf("  n = %d random ints\n", big_n);
    printf("  naive          = %lld   (%.3f s)\n", bn, naive_s);
    printf("  divide&conquer = %lld   (%.4f s)\n", bd, dc_s);
    printf("  -> same answer, and D&C is ~%.0fx faster here\n",
           dc_s > 0 ? naive_s / dc_s : 0.0);

    free(big);
    free(bigc);
    free(bigt);
    return 0;
}
