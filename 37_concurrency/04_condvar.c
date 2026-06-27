// Module 37 — Demo 4: Producer/consumer with a condition variable
//
// A bounded buffer (fixed-size ring) shared by a producer and a consumer. A
// mutex alone is not enough: the consumer must WAIT when the buffer is empty,
// and the producer must WAIT when it is full — without burning the CPU spinning.
// A *condition variable* gives us exactly that: pthread_cond_wait atomically
// releases the mutex and sleeps until another thread calls pthread_cond_signal.
// Build & run with: make run4
//
// The golden rule: always wait inside a `while (condition)` loop, never a plain
// `if` — a thread can wake spuriously or lose its slot to another waiter, so it
// must re-check the predicate after waking. Read alongside README.md §4.

#include <stdio.h>
#include <pthread.h>

#define CAP    4        // buffer holds at most 4 items
#define TOTAL  16       // produce this many items total

static int             buf[CAP];
static int             count = 0;   // items currently in the buffer
static int             head  = 0;   // next slot to read
static int             tail  = 0;   // next slot to write

static pthread_mutex_t lock     = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  not_full  = PTHREAD_COND_INITIALIZER;  // signalled by consumer
static pthread_cond_t  not_empty = PTHREAD_COND_INITIALIZER;  // signalled by producer

static void *producer(void *arg) {
    (void)arg;
    for (int i = 0; i < TOTAL; i++) {
        pthread_mutex_lock(&lock);
        while (count == CAP) {                 // buffer full -> wait for room
            pthread_cond_wait(&not_full, &lock);
        }
        buf[tail] = i;
        tail = (tail + 1) % CAP;
        count++;
        printf("  produced %2d   (buffer now holds %d)\n", i, count);
        pthread_cond_signal(&not_empty);       // wake a waiting consumer
        pthread_mutex_unlock(&lock);
    }
    return NULL;
}

static void *consumer(void *arg) {
    (void)arg;
    long sum = 0;
    for (int i = 0; i < TOTAL; i++) {
        pthread_mutex_lock(&lock);
        while (count == 0) {                   // buffer empty -> wait for data
            pthread_cond_wait(&not_empty, &lock);
        }
        int item = buf[head];
        head = (head + 1) % CAP;
        count--;
        sum += item;
        printf("           consumed %2d   (buffer now holds %d)\n", item, count);
        pthread_cond_signal(&not_full);        // wake a waiting producer
        pthread_mutex_unlock(&lock);
    }
    printf("\n  consumer received all %d items, sum = %ld (expected %d)\n",
           TOTAL, sum, TOTAL * (TOTAL - 1) / 2);
    return NULL;
}

int main(void) {
    printf("=== Bounded buffer (cap %d): 1 producer, 1 consumer, %d items ===\n",
           CAP, TOTAL);

    pthread_t p, c;
    pthread_create(&p, NULL, producer, NULL);
    pthread_create(&c, NULL, consumer, NULL);
    pthread_join(p, NULL);
    pthread_join(c, NULL);

    printf("\n  Done — no busy-waiting: idle threads slept on a condition var.\n");
    return 0;
}
