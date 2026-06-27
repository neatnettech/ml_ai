// Module 33 — Demo 4: Seeing the memory hierarchy (L1 / L2 / LLC / DRAM)
//
// Memory isn't one flat thing — it's a hierarchy of caches getting bigger and
// slower the further from the core you go:
//
//   registers  <  L1 (~64-128 KB, ~1 ns)  <  L2 (~MBs, ~3-5 ns)
//              <  last-level cache (~MBs-tens of MB)  <  DRAM (~60-100 ns)
//
// We reveal it with a POINTER-CHASE: shuffle a linked list of indices through a
// buffer of a given size, then chase the chain. Each step depends on the previous
// one (`idx = a[idx]`), so the CPU can't prefetch ahead — every access pays the
// true latency of wherever that buffer currently lives. Sweep the buffer size and
// the time-per-access steps UP each time the working set spills out of one cache
// level into the next.
//
// Build & run: make run4.  Read alongside README.md §4.
//
// NOTE: the exact step sizes are your machine's cache sizes; the STAIRCASE shape is
// universal. On unified-memory Apple Silicon the last step is the DRAM cliff.

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static volatile size_t sink;

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

// Build a random permutation cycle over `n` slots: a[i] holds the NEXT index to
// visit, so chasing `i = a[i]` visits every slot once before repeating. Random
// order defeats the hardware prefetcher, so each hop pays real latency.
static void make_random_cycle(size_t *a, size_t n) {
    for (size_t i = 0; i < n; i++) a[i] = i;
    // Fisher-Yates on the SEQUENCE of visits, then thread the chain.
    size_t *order = malloc(n * sizeof *order);
    for (size_t i = 0; i < n; i++) order[i] = i;
    for (size_t i = n - 1; i > 0; i--) {
        size_t j = (size_t)rand() % (i + 1);
        size_t tmp = order[i]; order[i] = order[j]; order[j] = tmp;
    }
    for (size_t i = 0; i < n; i++) a[order[i]] = order[(i + 1) % n];
    free(order);
}

int main(void) {
    srand(1);
    static const size_t kb_sizes[] = {
        4, 8, 16, 32, 64, 128, 256, 512,
        1024, 2048, 4096, 8192, 16384, 32768
    };
    const size_t nsizes = sizeof kb_sizes / sizeof *kb_sizes;
    const long HOPS = 64L * 1024 * 1024;  // fixed work per size

    printf("Pointer-chase latency vs working-set size.\n");
    printf("  size       ns/access\n");
    printf("  --------   ---------\n");

    for (size_t s = 0; s < nsizes; s++) {
        size_t bytes = kb_sizes[s] * 1024;
        size_t n = bytes / sizeof(size_t);
        size_t *a = malloc(n * sizeof *a);
        if (!a) { perror("malloc"); return 1; }
        make_random_cycle(a, n);

        // Warm the buffer into cache (for the small sizes) before timing.
        size_t idx = 0;
        for (size_t i = 0; i < n; i++) idx = a[idx];
        sink = idx;

        idx = 0;
        double t0 = now_sec();
        for (long h = 0; h < HOPS; h++) idx = a[idx];
        double dt = now_sec() - t0;
        sink = idx;  // forces the chase to actually happen

        if (kb_sizes[s] >= 1024)
            printf("  %4zu MiB   %8.2f\n", kb_sizes[s] / 1024, dt / (double)HOPS * 1e9);
        else
            printf("  %4zu KiB   %8.2f\n", kb_sizes[s], dt / (double)HOPS * 1e9);

        free(a);
    }

    printf("\nFlat regions = the working set fits in one cache level. Each step UP\n");
    printf("is a spill into the next, slower level: L1 -> L2 -> LLC -> DRAM.\n");

    return 0;
}
