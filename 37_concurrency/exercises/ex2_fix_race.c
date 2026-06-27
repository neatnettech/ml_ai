// Exercise 37.2 — Fix a racy counter
//
// The code below has the SAME data race as demo 2: many threads do `counter++`
// with no synchronization, so the final value comes out too low. Fix it so the
// final value is always exactly N_THREADS * PER_THREAD.
//
// Pick ONE of the two fixes you learned:
//   (a) a pthread_mutex_t around the increment (see demo 3), OR
//   (b) make `counter` an atomic_long + atomic_fetch_add (see demo 5).
// Solution in ../solutions/ex2_fix_race.c uses the atomic approach.

#include <stdio.h>
#include <pthread.h>

#define N_THREADS    8
#define PER_THREAD   500000L

// TODO: change the type / add a lock so the increment below is safe.
static long counter = 0;

static void *increment(void *arg) {
    (void)arg;
    for (long i = 0; i < PER_THREAD; i++) {
        // TODO: make this increment safe under concurrency.
        counter++;
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

    long expected = (long)N_THREADS * PER_THREAD;
    printf("final counter = %ld\n", (long)counter);
    printf("expected      = %ld\n", expected);
    printf("correct       = %s\n", (long)counter == expected ? "yes" : "NO (race not fixed)");

    return 0;
}
