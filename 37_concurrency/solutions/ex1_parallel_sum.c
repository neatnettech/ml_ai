// SOLUTION 37.1 — Parallel array sum

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

#define N_THREADS 4
#define N         2000000

typedef struct {
    const long *data;
    long        start;
    long        end;
    long        result;
} Slice;

static void *sum_slice(void *arg) {
    Slice *s = (Slice *)arg;
    long acc = 0;
    for (long i = s->start; i < s->end; i++) {
        acc += s->data[i];
    }
    s->result = acc;
    return NULL;
}

int main(void) {
    long *data = malloc((size_t)N * sizeof *data);
    if (!data) { perror("malloc"); return 1; }
    long serial = 0;
    for (long i = 0; i < N; i++) { data[i] = i % 100; serial += data[i]; }

    pthread_t threads[N_THREADS];
    Slice     slices[N_THREADS];
    const long chunk = N / N_THREADS;

    for (int i = 0; i < N_THREADS; i++) {
        slices[i].data   = data;
        slices[i].start  = (long)i * chunk;
        slices[i].end    = (i == N_THREADS - 1) ? N : (long)(i + 1) * chunk;
        slices[i].result = 0;
        pthread_create(&threads[i], NULL, sum_slice, &slices[i]);
    }

    long parallel = 0;
    for (int i = 0; i < N_THREADS; i++) {
        pthread_join(threads[i], NULL);
        parallel += slices[i].result;
    }

    printf("serial sum   = %ld\n", serial);
    printf("parallel sum = %ld\n", parallel);
    printf("match        = %s\n", serial == parallel ? "yes" : "NO");

    free(data);
    return 0;
}
