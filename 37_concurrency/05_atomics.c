// Module 37 — Demo 5: A lock-free counter with C11 atomics
//
// Same race as demo 2, fixed a third way: make the counter an `atomic_long` and
// increment it with `atomic_fetch_add`. The hardware performs the load-add-store
// as ONE indivisible operation, so no update can be lost — without any mutex.
// Build & run with: make run5
//
// Versus the mutex (demo 3): the code is simpler (no lock to acquire, hold, and
// remember to release; no risk of deadlock — see exercise 3) and for a single
// counter it is usually faster, since there is no blocking. Atomics shine for
// small lock-free operations on one variable; a mutex is what you reach for once
// a critical section touches *several* variables together. Read README.md §5.

#include <stdio.h>
#include <pthread.h>
#include <stdatomic.h>

#define N_THREADS    8
#define PER_THREAD   1000000L

// `_Atomic` makes every access an atomic operation; atomic_fetch_add is the
// indivisible read-modify-write. memory_order is left at the default
// (sequentially consistent) for clarity.
static atomic_long counter = 0;

static void *increment(void *arg) {
    (void)arg;
    for (long i = 0; i < PER_THREAD; i++) {
        atomic_fetch_add(&counter, 1);   // indivisible: no update can be lost
    }
    return NULL;
}

int main(void) {
    pthread_t threads[N_THREADS];

    printf("=== %d threads, atomic_fetch_add %ld times each (lock-free) ===\n",
           N_THREADS, PER_THREAD);

    for (int i = 0; i < N_THREADS; i++) {
        pthread_create(&threads[i], NULL, increment, NULL);
    }
    for (int i = 0; i < N_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    long final    = atomic_load(&counter);
    long expected = (long)N_THREADS * PER_THREAD;
    printf("\n  final counter = %ld\n", final);
    printf("  expected      = %ld  (%s)\n", expected,
           final == expected ? "correct" : "STILL WRONG");
    printf("\n  Correct every run, no mutex, no critical section to forget.\n");

    return 0;
}
