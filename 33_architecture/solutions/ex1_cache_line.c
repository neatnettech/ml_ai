// SOLUTION 33.1 — Estimate the cache line size from a stride sweep
//
// The elbow (where ns/access stops rising) marks the line size: below it, several
// strided touches share one fetched line; at/above it, each touch needs its own.

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define ARRAY_BYTES (64 * 1024 * 1024)
#define NELEM       (ARRAY_BYTES / (int)sizeof(int))

static volatile long long sink;

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

int main(void) {
    int *a = malloc((size_t)NELEM * sizeof *a);
    if (!a) { perror("malloc"); return 1; }
    for (int i = 0; i < NELEM; i++) a[i] = i;

    const long TOUCHES = 16L * 1024 * 1024;

    printf("  stride(bytes)   ns/access\n");
    printf("  -------------   ---------\n");
    for (int stride = 1; stride <= 64; stride *= 2) {
        long long acc = 0;
        long idx = 0;
        double t0 = now_sec();
        for (long t = 0; t < TOUCHES; t++) {
            acc += a[idx];
            idx = (idx + stride) & (NELEM - 1);
        }
        double dt = now_sec() - t0;
        sink = acc;
        printf("  %9d       %8.2f\n", stride * (int)sizeof(int),
               dt / (double)TOUCHES * 1e9);
    }

    printf("\nRead the elbow: the stride where cost stops climbing ~ the line size.\n");

    free(a);
    return 0;
}
