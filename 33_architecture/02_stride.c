// Module 33 — Demo 2: Finding the cache LINE size with a stride experiment
//
// Touch one int every `stride` ints across a big array, doing the same TOTAL number
// of touches each time. While stride <= line size, several of your touches land on
// the same line that was already fetched, so time-per-touch stays low. Once stride
// >= line size, every touch is a brand-new line: time-per-touch stops growing and
// plateaus. The stride where the cost flattens out ~ the cache line size (~64 B on
// Apple Silicon and x86-64; 128 B on some Apple cores).
//
// Build & run: make run2.  Read alongside README.md §2.
//
// NOTE: the elbow's exact location varies by machine; the SHAPE is the lesson.

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define ARRAY_BYTES (64 * 1024 * 1024)              // 64 MiB working set
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

    // Keep total work constant: always do the same number of accesses regardless
    // of stride, so we measure cost-per-access, not how many accesses we did.
    const long TOUCHES = 16L * 1024 * 1024;

    printf("Array %d MiB, %ld touches per run.\n",
           ARRAY_BYTES / (1024 * 1024), TOUCHES);
    printf("  stride(bytes)   ns/access\n");
    printf("  -------------   ---------\n");

    for (int stride = 1; stride <= 64; stride *= 2) {
        long long acc = 0;
        // Walk the array in steps of `stride` ints, wrapping with a mask. NELEM is
        // a power of two, so (idx & (NELEM-1)) wraps cheaply without a branch.
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

    printf("\nCost climbs while stride < line size (touches share a fetched line),\n");
    printf("then flattens once each touch needs its own line. The elbow ~ line size.\n");

    free(a);
    return 0;
}
