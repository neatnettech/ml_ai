// Module 33 — Demo 1: Spatial locality (row-major vs column-major)
//
// A 2D array in C is stored row-major: a[i][0], a[i][1], ... are contiguous in
// memory. The CPU never fetches one byte; it fetches a whole CACHE LINE (~64 B).
// Summing row-major rides along each line; summing column-major jumps a whole row
// between accesses, so every access is (almost) a fresh line. Same arithmetic,
// same number of additions — the only difference is the memory ACCESS ORDER.
//
// Build & run: make run1.  Read alongside README.md §1.
//
// NOTE: absolute numbers depend on your machine; the RATIO is the lesson.

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 4096   // N*N ints = 4096*4096*4 bytes = 64 MiB, far bigger than any cache

// A volatile sink: writing the result here stops the optimizer from deleting the
// whole loop (it can't prove the store is unobservable).
static volatile long long sink;

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

int main(void) {
    int *a = malloc((size_t)N * N * sizeof *a);
    if (!a) { perror("malloc"); return 1; }

    // Fill it (also warms the allocation so the timed loops aren't paying for
    // first-touch page faults).
    for (long i = 0; i < (long)N * N; i++) a[i] = (int)(i & 7);

    // --- Row-major: inner loop walks j, i.e. consecutive addresses ---
    double t0 = now_sec();
    long long row_sum = 0;
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            row_sum += a[i * N + j];
    double row_time = now_sec() - t0;
    sink = row_sum;

    // --- Column-major: inner loop walks i, jumping N ints (one full row) each step ---
    t0 = now_sec();
    long long col_sum = 0;
    for (int j = 0; j < N; j++)
        for (int i = 0; i < N; i++)
            col_sum += a[i * N + j];
    double col_time = now_sec() - t0;
    sink = col_sum;

    printf("Array: %d x %d ints  (%.0f MiB)\n",
           N, N, (double)N * N * sizeof(int) / (1024.0 * 1024.0));
    printf("  row-major sum   : %.4f s   (sum=%lld)\n", row_time, row_sum);
    printf("  column-major sum: %.4f s   (sum=%lld)\n", col_time, col_sum);
    printf("  ratio (col / row): %.2fx slower column-major\n",
           col_time / row_time);
    printf("\nSame %lld additions either way — only the access ORDER differs.\n",
           (long long)N * N);
    printf("Row-major rides each 64-byte cache line; column-major touches a new\n");
    printf("line almost every access, so it pays the memory system far more often.\n");

    free(a);
    return 0;
}
