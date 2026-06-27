// Module 33 — Demo 3: Branch prediction (the famous sorted-vs-unsorted test)
//
// A modern CPU is pipelined: it starts executing the instructions AFTER a branch
// before it knows which way the branch goes, by PREDICTING the outcome. Predict
// right and the pipeline stays full. Predict wrong and it must flush the wrongly
// fetched instructions and restart — a penalty of ~15-20 cycles.
//
// Here we sum the elements above a threshold. The `if (data[i] >= T)` branch is the
// hot spot. On a SORTED array the branch is false, false, ..., then true, true, ...
// — one switch the predictor learns instantly. On a SHUFFLED array it's ~50/50 and
// essentially unpredictable, so the CPU mispredicts about half the time.
//
// Same data, same comparisons, same additions — only the ORDER changes, yet sorted
// runs several times faster. (Reference: Stack Overflow's most-upvoted question.)
//
// Build & run: make run3.  Read alongside README.md §3.

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N        (1 << 22)   // 4,194,304 elements
#define REPEATS  64          // repeat to make the timing comfortably measurable
#define THRESHOLD 128

static volatile long long sink;

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

// Sum every element >= THRESHOLD. The `if` is the branch under study.
//
// IMPORTANT (and itself an architecture lesson): at -O2 the compiler is smart
// enough to turn `if (cond) sum += x;` into a BRANCHLESS conditional-select +
// SIMD reduction — there's then no branch left to mispredict, so sorted and
// unsorted run at the SAME speed. To actually OBSERVE branch prediction we must
// keep a real data-dependent branch:
//   * `#pragma clang loop vectorize(disable)` stops the SIMD reduction, and
//   * the compiler barrier on the taken path stops if-conversion into a select.
// Comment those two lines out and re-time: the gap collapses — that is the
// compiler defeating the very effect we're studying.
static long long sum_above(const int *data, int n) {
    long long sum = 0;
#pragma clang loop vectorize(disable)
    for (int i = 0; i < n; i++) {
        if (data[i] >= THRESHOLD) {
            sum += data[i];
            __asm__ volatile("" : "+r"(sum) :: "memory");  // barrier: keep the branch
        }
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

    srand(1);  // fixed seed: reproducible run-to-run
    for (int i = 0; i < N; i++) data[i] = rand() % 256;  // values 0..255

    // --- UNSORTED: branch outcome is ~50/50, hard to predict ---
    double t0 = now_sec();
    long long unsorted_sum = 0;
    for (int r = 0; r < REPEATS; r++) unsorted_sum += sum_above(data, N);
    double unsorted_time = now_sec() - t0;
    sink = unsorted_sum;

    // --- SORTED: branch is false...false, true...true — one easy transition ---
    qsort(data, N, sizeof *data, cmp_int);
    t0 = now_sec();
    long long sorted_sum = 0;
    for (int r = 0; r < REPEATS; r++) sorted_sum += sum_above(data, N);
    double sorted_time = now_sec() - t0;
    sink = sorted_sum;

    printf("%d elements, %d repeats, threshold %d.\n", N, REPEATS, THRESHOLD);
    printf("  unsorted: %.4f s   (sum=%lld)\n", unsorted_time, unsorted_sum);
    printf("  sorted  : %.4f s   (sum=%lld)\n", sorted_time, sorted_sum);
    printf("  ratio (unsorted / sorted): %.2fx slower when unpredictable\n",
           unsorted_time / sorted_time);
    printf("\nIdentical work, identical sums. The shuffled array makes the\n");
    printf("`if` branch unpredictable, so the CPU mispredicts ~half the time and\n");
    printf("flushes the pipeline on every miss.\n");

    free(data);
    return 0;
}
