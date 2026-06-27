// SOLUTION 33.3 — Matrix multiply ijk vs ikj
//
// Why ikj wins: with k as the MIDDLE loop, the inner j-loop sweeps B[k][j] and
// C[i][j] across rows (stride 1), while A[i][k] is loop-invariant in j. Every inner
// step rides the cache line just fetched. In ijk, the inner k-loop walks B[k][j]
// down a column (stride N), missing the cache on almost every access.

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 512

static volatile double sink;

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

int main(void) {
    double *A = malloc((size_t)N * N * sizeof *A);
    double *B = malloc((size_t)N * N * sizeof *B);
    double *C = malloc((size_t)N * N * sizeof *C);
    if (!A || !B || !C) { perror("malloc"); return 1; }
    for (int i = 0; i < N * N; i++) { A[i] = (i % 7) * 0.5; B[i] = (i % 5) * 0.25; }

    for (int i = 0; i < N * N; i++) C[i] = 0.0;
    double t0 = now_sec();
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            for (int k = 0; k < N; k++)
                C[i * N + j] += A[i * N + k] * B[k * N + j];
    double ijk_time = now_sec() - t0;
    sink = C[(N - 1) * N + (N - 1)];

    for (int i = 0; i < N * N; i++) C[i] = 0.0;
    t0 = now_sec();
    for (int i = 0; i < N; i++)
        for (int k = 0; k < N; k++)
            for (int j = 0; j < N; j++)
                C[i * N + j] += A[i * N + k] * B[k * N + j];
    double ikj_time = now_sec() - t0;
    sink = C[(N - 1) * N + (N - 1)];

    printf("%dx%d double matmul:\n", N, N);
    printf("  ijk: %.4f s\n", ijk_time);
    printf("  ikj: %.4f s\n", ikj_time);
    printf("  speedup (ijk / ikj): %.2fx\n",
           ikj_time > 0 ? ijk_time / ikj_time : 0.0);
    printf("\nikj keeps the inner loop stride-1 over B and C; ijk strides down a\n");
    printf("column of B and misses cache nearly every inner step.\n");

    free(A); free(B); free(C);
    return 0;
}
