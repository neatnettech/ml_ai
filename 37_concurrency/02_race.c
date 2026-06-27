// Module 37 — Demo 2: A data race (the teaching BUG)
//
// Several threads increment the SAME shared `long` with no synchronization.
// `counter++` looks atomic but is really three steps: load, add 1, store. When
// two threads interleave those steps, one update overwrites the other and is
// lost. The final value is therefore TOO LOW and *non-deterministic* — run it
// twice and you usually get two different wrong answers. Build & run: make run2
//
// This is a real bug. Demos 3 (mutex) and 5 (atomics) fix it.
// Read alongside README.md §2.

#include <stdio.h>
#include <pthread.h>

#define N_THREADS    8
#define PER_THREAD   1000000L

// Shared, mutable, and touched by every thread with no protection: a data race.
static long counter = 0;

static void *increment(void *arg) {
    (void)arg;
    for (long i = 0; i < PER_THREAD; i++) {
        counter++;   // load -> add 1 -> store : NOT atomic, updates get lost
    }
    return NULL;
}

int main(void) {
    pthread_t threads[N_THREADS];

    printf("=== %d threads each do counter++ %ld times ===\n",
           N_THREADS, PER_THREAD);

    for (int i = 0; i < N_THREADS; i++) {
        pthread_create(&threads[i], NULL, increment, NULL);
    }
    for (int i = 0; i < N_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    long expected = (long)N_THREADS * PER_THREAD;
    printf("\n  final counter = %ld\n", counter);
    printf("  expected      = %ld\n", expected);
    printf("  lost updates  = %ld  (%s)\n", expected - counter,
           counter == expected ? "no race observed this run" : "RACE: updates lost");
    printf("\n  Re-run `make run2` — the wrong value is non-deterministic.\n");

    return 0;
}
