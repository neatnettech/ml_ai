// Exercise 33.2 — Reproduce the sorted-vs-unsorted branch timing
//
// Recreate demo 3 on your own: time `sum_above` over a SHUFFLED array and over a
// SORTED copy of the same data, then report the speedup. Fill in the two timed
// regions. Run `make ex2`; the unsorted run should be several times slower because
// its `if` branch is unpredictable and the pipeline flushes on every misprediction.
//
// Compare against `make sol2`.

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N        (1 << 22)
#define REPEATS  64
#define THRESHOLD 128

static volatile long long sink;

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

// The pragma + barrier keep a real data-dependent branch; at -O2 the compiler
// would otherwise make this branchless (see demo 3) and the effect would vanish.
static long long sum_above(const int *data, int n) {
    long long sum = 0;
#pragma clang loop vectorize(disable)
    for (int i = 0; i < n; i++)
        if (data[i] >= THRESHOLD) {
            sum += data[i];
            __asm__ volatile("" : "+r"(sum) :: "memory");
        }
    return sum;
}

static int cmp_int(const void *a, const void *b) {
    int x = *(const int *)a, y = *(const int *)b;
    return (x > y) - (x < y);
}

int main(void) {
    int *data = malloc((size_t)N * sizeof *data);
    if (!data) { perror("malloc"); return 1; }
    srand(1);
    for (int i = 0; i < N; i++) data[i] = rand() % 256;

    // Until you fill in the TODOs, these keep the helpers "used" so the stub
    // compiles warning-free. Remove them once your timed loops call now_sec()/sum_above().
    (void)now_sec; (void)sum_above;

    // TODO (unsorted): time REPEATS calls to sum_above over the shuffled `data`.
    //   Record the elapsed seconds in `unsorted_time` and the sum in `unsorted_sum`.
    double unsorted_time = 0.0;
    long long unsorted_sum = 0;

    qsort(data, N, sizeof *data, cmp_int);

    // TODO (sorted): same measurement, now that `data` is sorted.
    //   Record `sorted_time` and `sorted_sum`. Assign a sum to `sink` so the
    //   compiler can't optimize the loops away.
    double sorted_time = 0.0;
    long long sorted_sum = 0;

    sink = unsorted_sum + sorted_sum;
    printf("  unsorted: %.4f s\n", unsorted_time);
    printf("  sorted  : %.4f s\n", sorted_time);
    printf("  speedup (unsorted / sorted): %.2fx\n",
           sorted_time > 0 ? unsorted_time / sorted_time : 0.0);

    free(data);
    return 0;
}
