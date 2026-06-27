// Module 37 — Demo 1: Spawning threads and joining them
//
// A *thread* is an independent flow of execution that shares the same address
// space (globals, heap) with the other threads of the process — that shared
// memory is what makes them powerful AND dangerous (see demo 2). Here we just
// spawn N worker threads, give each its own argument struct, let them run in
// parallel, join them, and collect their results. Build & run with: make run1
//
// Read top to bottom alongside README.md §1.

#include <stdio.h>
#include <pthread.h>

#define N_THREADS 4

// Each thread gets its OWN argument struct, so there is no sharing of mutable
// state — the clean, race-free way to pass data in and results out.
typedef struct {
    int   id;        // which worker am I (0..N-1)
    long  start;     // sum the integers in [start, end)
    long  end;
    long  result;    // the worker writes its partial sum here
} Work;

// The function every thread runs. pthreads requires the signature
// `void *(*)(void *)`, so we take a void* and cast it back to our struct.
static void *worker(void *arg) {
    Work *w = (Work *)arg;
    long sum = 0;
    for (long i = w->start; i < w->end; i++) {
        sum += i;
    }
    w->result = sum;
    printf("  thread %d summed [%ld, %ld) -> %ld\n", w->id, w->start, w->end, sum);
    return NULL;
}

int main(void) {
    pthread_t threads[N_THREADS];
    Work      work[N_THREADS];
    const long chunk = 1000000;  // each thread sums a 1,000,000-wide slice

    printf("=== Spawning %d threads, each summing a slice ===\n", N_THREADS);

    // Launch all threads. pthread_create returns 0 on success; the new thread
    // begins executing worker() immediately, possibly before this loop finishes.
    for (int i = 0; i < N_THREADS; i++) {
        work[i].id     = i;
        work[i].start  = (long)i * chunk;
        work[i].end    = (long)(i + 1) * chunk;
        work[i].result = 0;
        pthread_create(&threads[i], NULL, worker, &work[i]);
    }

    // Join = wait for each thread to finish. Without this the process could exit
    // (or read results) before the workers are done. Joining is also how we know
    // it is safe to read work[i].result.
    long total = 0;
    for (int i = 0; i < N_THREADS; i++) {
        pthread_join(threads[i], NULL);
        total += work[i].result;
    }

    printf("\n  combined total = %ld\n", total);

    // Cross-check against the closed-form sum 0+1+...+(M-1) = M*(M-1)/2.
    long m = (long)N_THREADS * chunk;
    long expected = m * (m - 1) / 2;
    printf("  expected       = %ld  (%s)\n", expected,
           total == expected ? "match" : "MISMATCH");

    return 0;
}
