// Exercise 37.3 — Deadlock, and how to avoid it
//
// DEADLOCK happens when two threads each hold a lock the other needs and neither
// will let go. Classic recipe with two mutexes A and B:
//
//     thread 1: lock(A); lock(B); ...      thread 2: lock(B); lock(A); ...
//
// If thread 1 grabs A while thread 2 grabs B, then thread 1 waits forever for B
// and thread 2 waits forever for A. The program hangs (no output, no exit) — you
// would have to Ctrl-C it.
//
// THE FIX: a global LOCK ORDERING. If every thread always locks A before B
// (never B before A), no wait cycle can form and deadlock is impossible.
//
// So this exercise can never hang the default `make ex3`, the real bug is gated
// behind `-DDEADLOCK`: that flag both selects worker_two's reversed lock order
// AND lets the two threads run concurrently, reproducing the hang. WITHOUT the
// flag, worker_two uses the correct order, so it is safe even concurrently.
// Build the hang on purpose with:  clang -std=c11 -pthread -DDEADLOCK ...
// The committed build must NEVER define DEADLOCK. Solution in ../solutions/.
//
// TODO: complete worker_two's SAFE branch so it locks mutex_a first, then
// mutex_b — the same order worker_one uses.

#include <stdio.h>
#include <pthread.h>
#ifdef DEADLOCK
#include <unistd.h>   // usleep, only to widen the race window for the demo
#endif

static pthread_mutex_t mutex_a = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t mutex_b = PTHREAD_MUTEX_INITIALIZER;

static void *worker_one(void *arg) {
    (void)arg;
    pthread_mutex_lock(&mutex_a);
#ifdef DEADLOCK
    usleep(1000);   // hold A a moment so worker_two can grab B -> wait cycle
#endif
    pthread_mutex_lock(&mutex_b);
    printf("  worker_one: locked A then B, does its work\n");
    pthread_mutex_unlock(&mutex_b);
    pthread_mutex_unlock(&mutex_a);
    return NULL;
}

static void *worker_two(void *arg) {
    (void)arg;
#ifdef DEADLOCK
    // BUGGY order — opposite of worker_one. Combined with concurrent execution
    // (see main) this is the classic deadlock. Never ship this.
    pthread_mutex_lock(&mutex_b);
    usleep(1000);   // hold B a moment so worker_one is stuck on B -> wait cycle
    pthread_mutex_lock(&mutex_a);
    printf("  worker_two: locked B then A, does its work\n");
    pthread_mutex_unlock(&mutex_a);
    pthread_mutex_unlock(&mutex_b);
#else
    // TODO: lock mutex_a FIRST, then mutex_b (same order as worker_one), then
    // unlock in reverse. Right now the two lock lines are reversed — fix them.
    pthread_mutex_lock(&mutex_b);   // <-- should be mutex_a
    pthread_mutex_lock(&mutex_a);   // <-- should be mutex_b
    printf("  worker_two: locked A then B, does its work\n");
    pthread_mutex_unlock(&mutex_b);
    pthread_mutex_unlock(&mutex_a);
#endif
    return NULL;
}

int main(void) {
    printf("=== Two mutexes, two threads ===\n");
    pthread_t t1, t2;

#ifdef DEADLOCK
    // Run BOTH threads concurrently with the reversed order above -> may hang.
    printf("  (built with -DDEADLOCK: reversed orders, concurrent -> may hang)\n");
    pthread_create(&t1, NULL, worker_one, NULL);
    pthread_create(&t2, NULL, worker_two, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
#else
    // Safe build. We run the two workers one-after-another (join t1 before
    // starting t2) so this stub can NEVER hang while you are still completing
    // the TODO above. Once you fix worker_two to lock A-before-B, the consistent
    // ordering makes it deadlock-free even if you later run them concurrently.
    pthread_create(&t1, NULL, worker_one, NULL);
    pthread_join(t1, NULL);
    pthread_create(&t2, NULL, worker_two, NULL);
    pthread_join(t2, NULL);
#endif

    printf("\n  Both threads finished — no deadlock with consistent A-before-B order.\n");
    return 0;
}
