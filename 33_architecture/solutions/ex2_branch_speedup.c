// SOLUTION 33.2 — Sorted-vs-unsorted branch timing and speedup

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
// would otherwise make this branchless (see demo 3's comment) and the effect
// would vanish.
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

    double t0 = now_sec();
    long long unsorted_sum = 0;
    for (int r = 0; r < REPEATS; r++) unsorted_sum += sum_above(data, N);
    double unsorted_time = now_sec() - t0;

    qsort(data, N, sizeof *data, cmp_int);

    t0 = now_sec();
    long long sorted_sum = 0;
    for (int r = 0; r < REPEATS; r++) sorted_sum += sum_above(data, N);
    double sorted_time = now_sec() - t0;

    sink = unsorted_sum + sorted_sum;
    printf("  unsorted: %.4f s\n", unsorted_time);
    printf("  sorted  : %.4f s\n", sorted_time);
    printf("  speedup (unsorted / sorted): %.2fx\n",
           sorted_time > 0 ? unsorted_time / sorted_time : 0.0);

    free(data);
    return 0;
}
