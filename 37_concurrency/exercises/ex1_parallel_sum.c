// Exercise 37.1 — Parallel array sum
//
// Sum a large array with N threads: each thread sums one contiguous SLICE, then
// main combines the partial sums. Verify the parallel total equals the serial
// total. Implement the two TODOs below. `make sol1` shows the expected output.
//
// Key idea: give each thread its OWN argument struct (its slice + a result
// field). No shared mutable state -> no race -> no lock needed. Solution in
// ../solutions/ex1_parallel_sum.c.

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

#define N_THREADS 4
#define N         2000000

typedef struct {
    const long *data;
    long        start;   // sum data[start .. end)
    long        end;
    long        result;  // write the partial sum here
} Slice;

static void *sum_slice(void *arg) {
    Slice *s = (Slice *)arg;
    // TODO: sum data[start .. end) into a local variable and store it in s->result.
    // Hint: long acc = 0; for (long i = s->start; i < s->end; i++) acc += s->data[i];
    (void)s;  // remove this line once you use s
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
        // TODO: join thread i, then add slices[i].result to `parallel`.
    }

    printf("serial sum   = %ld\n", serial);
    printf("parallel sum = %ld\n", parallel);
    printf("match        = %s\n", serial == parallel ? "yes" : "NO");

    free(data);
    return 0;
}
