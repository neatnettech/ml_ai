// Exercise 33.3 — Matrix multiply: ijk vs ikj loop order
//
// C = A * B for square n x n matrices, stored row-major. The arithmetic is the same
// for any loop order, but the ACCESS pattern of the innermost loop is not:
//
//   ijk: inner loop k walks B[k][j] DOWN a column -> stride n -> cache-hostile.
//   ikj: inner loop j walks B[k][j] ACROSS a row  -> stride 1 -> cache-friendly,
//        and C[i][j] is also swept across a row.
//
// Fill in the two triple loops, run `make ex3`, and confirm ikj is faster. Explain
// why in one line of your own. Compare against `make sol3`.

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 512   // 512x512 doubles per matrix = 2 MiB each

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

    // --- ijk order ---
    for (int i = 0; i < N * N; i++) C[i] = 0.0;
    double t0 = now_sec();
    // TODO (ijk): for i, for j, for k:  C[i*N+j] += A[i*N+k] * B[k*N+j];
    double ijk_time = now_sec() - t0;
    sink = C[(N - 1) * N + (N - 1)];

    // --- ikj order ---
    for (int i = 0; i < N * N; i++) C[i] = 0.0;
    t0 = now_sec();
    // TODO (ikj): for i, for k, for j:  C[i*N+j] += A[i*N+k] * B[k*N+j];
    double ikj_time = now_sec() - t0;
    sink = C[(N - 1) * N + (N - 1)];

    printf("%dx%d double matmul:\n", N, N);
    printf("  ijk: %.4f s\n", ijk_time);
    printf("  ikj: %.4f s\n", ikj_time);
    printf("  speedup (ijk / ikj): %.2fx\n",
           ikj_time > 0 ? ijk_time / ikj_time : 0.0);

    free(A); free(B); free(C);
    return 0;
}
