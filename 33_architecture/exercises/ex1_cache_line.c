// Exercise 33.1 — Estimate your machine's cache line size
//
// Demo 2 walked an array in increasing strides and watched cost-per-access climb,
// then flatten once each access needs its own cache line. Here you write the timed
// loop yourself. Fill in the TODO, run `make ex1`, and read the elbow off the table:
// the byte-stride where ns/access stops rising ~ your cache line size (often 64,
// sometimes 128 on Apple performance cores).
//
// Compare against `make sol1`.

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

        // TODO: do exactly TOUCHES accesses, each time:
        //   - add a[idx] into acc
        //   - advance idx by `stride`, wrapping with (idx & (NELEM - 1))
        // Hint: NELEM is a power of two, so the mask wraps without a branch.
        // (Keep `acc` and assign it to `sink` afterwards so the loop isn't deleted.)
        (void)idx;  // remove this line once you use idx in the loop

        double dt = now_sec() - t0;
        sink = acc;
        printf("  %9d       %8.2f\n", stride * (int)sizeof(int),
               dt / (double)TOUCHES * 1e9);
    }

    free(a);
    return 0;
}
