// SOLUTION 37.2 — Fix a racy counter (atomic approach)
//
// One-line fix: make the counter atomic and use atomic_fetch_add. The increment
// is now an indivisible read-modify-write, so no update is ever lost. (The mutex
// approach from demo 3 is equally correct — wrap counter++ in lock/unlock.)

#include <stdio.h>
#include <pthread.h>
#include <stdatomic.h>

#define N_THREADS    8
#define PER_THREAD   500000L

static atomic_long counter = 0;   // was: long counter

static void *increment(void *arg) {
    (void)arg;
    for (long i = 0; i < PER_THREAD; i++) {
        atomic_fetch_add(&counter, 1);   // was: counter++
    }
    return NULL;
}

int main(void) {
    pthread_t threads[N_THREADS];

    for (int i = 0; i < N_THREADS; i++) {
        pthread_create(&threads[i], NULL, increment, NULL);
    }
    for (int i = 0; i < N_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    long final    = atomic_load(&counter);
    long expected = (long)N_THREADS * PER_THREAD;
    printf("final counter = %ld\n", final);
    printf("expected      = %ld\n", expected);
    printf("correct       = %s\n", final == expected ? "yes" : "NO (race not fixed)");

    return 0;
}
