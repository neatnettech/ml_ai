// SOLUTION 37.3 — Deadlock avoided by consistent lock ordering
//
// The fix is a single rule applied everywhere: ALWAYS lock mutex_a before
// mutex_b. Below, both worker_one and worker_two follow A-before-B, so the two
// threads can run fully concurrently and never form a wait cycle — no deadlock.
//
// What a deadlock would look like (the bug): if worker_two locked B then A while
// worker_one locked A then B, and both ran at once, thread 1 could hold A waiting
// for B while thread 2 holds B waiting for A — both stuck forever, the program
// hangs with no output and no exit (you would Ctrl-C it). You can reproduce that
// hang by building this file's exercise stub with `-DDEADLOCK`.

#include <stdio.h>
#include <pthread.h>

static pthread_mutex_t mutex_a = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t mutex_b = PTHREAD_MUTEX_INITIALIZER;

static void *worker_one(void *arg) {
    (void)arg;
    pthread_mutex_lock(&mutex_a);     // A first
    pthread_mutex_lock(&mutex_b);     // then B
    printf("  worker_one: locked A then B, does its work\n");
    pthread_mutex_unlock(&mutex_b);
    pthread_mutex_unlock(&mutex_a);
    return NULL;
}

static void *worker_two(void *arg) {
    (void)arg;
    pthread_mutex_lock(&mutex_a);     // SAME order: A first
    pthread_mutex_lock(&mutex_b);     // then B
    printf("  worker_two: locked A then B, does its work\n");
    pthread_mutex_unlock(&mutex_b);
    pthread_mutex_unlock(&mutex_a);
    return NULL;
}

int main(void) {
    printf("=== Two mutexes, two threads — consistent A-before-B ordering ===\n");
    pthread_t t1, t2;
    // Both threads run concurrently; consistent ordering keeps it safe.
    pthread_create(&t1, NULL, worker_one, NULL);
    pthread_create(&t2, NULL, worker_two, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    printf("\n  Both threads finished — no deadlock (consistent A-before-B order).\n");
    return 0;
}
