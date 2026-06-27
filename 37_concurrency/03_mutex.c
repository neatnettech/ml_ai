// Module 37 — Demo 3: Fixing the race with a mutex
//
// Same workload as demo 2, but the increment is wrapped in a *mutex* (mutual
// exclusion lock). pthread_mutex_lock blocks until this thread is the sole
// owner; only then does it touch `counter`; pthread_mutex_unlock lets the next
// thread in. The load-add-store is now a *critical section* that runs without
// interruption, so no updates are lost and the total is exact every run.
// Build & run with: make run3
//
// The cost: locking/unlocking a million times per thread serializes the work
// and is far slower than demo 1's independent slices — that is the price of
// sharing one location. Read alongside README.md §3.

#include <stdio.h>
#include <pthread.h>

#define N_THREADS    8
#define PER_THREAD   1000000L

static long            counter = 0;
static pthread_mutex_t lock    = PTHREAD_MUTEX_INITIALIZER;

static void *increment(void *arg) {
    (void)arg;
    for (long i = 0; i < PER_THREAD; i++) {
        pthread_mutex_lock(&lock);     // enter critical section (wait if needed)
        counter++;                     // now exclusive: load-add-store is safe
        pthread_mutex_unlock(&lock);   // leave; wake the next waiter
    }
    return NULL;
}

int main(void) {
    pthread_t threads[N_THREADS];

    printf("=== %d threads, counter++ %ld times each, GUARDED by a mutex ===\n",
           N_THREADS, PER_THREAD);

    for (int i = 0; i < N_THREADS; i++) {
        pthread_create(&threads[i], NULL, increment, NULL);
    }
    for (int i = 0; i < N_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    long expected = (long)N_THREADS * PER_THREAD;
    printf("\n  final counter = %ld\n", counter);
    printf("  expected      = %ld  (%s)\n", expected,
           counter == expected ? "correct" : "STILL WRONG");
    printf("\n  Correct every run — but the lock serializes the increments,\n");
    printf("  so this is noticeably slower than the unsynchronized version.\n");

    return 0;
}
