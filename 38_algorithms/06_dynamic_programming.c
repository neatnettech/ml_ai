// Module 38 — Demo 6: Dynamic programming
//
// DP solves a problem by combining solutions to overlapping subproblems, each
// computed ONCE and reused. We show it two ways:
//   1. Fibonacci: naive recursion recomputes the same values exponentially often;
//      memoization caches them, collapsing O(2^n) calls down to O(n).
//   2. 0/1 knapsack: a real optimization problem solved with a DP table — pick
//      items to maximize value within a weight budget.
// We COUNT function calls so the naive-vs-DP blowup is a number you can read.
// Build & run with: make run6
//
// Read top to bottom alongside README.md §6.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ===== Fibonacci: naive recursion vs memoized DP ============================
static long g_naive_calls;     // counts every fib_naive invocation
static long g_memo_calls;      // counts every fib_memo invocation

static long fib_naive(int n) {
    g_naive_calls++;
    if (n < 2) return n;
    return fib_naive(n - 1) + fib_naive(n - 2);    // recomputes everything
}

static long fib_memo(int n, long *cache) {
    g_memo_calls++;
    if (n < 2) return n;
    if (cache[n] != -1) return cache[n];           // already solved? reuse it
    cache[n] = fib_memo(n - 1, cache) + fib_memo(n - 2, cache);
    return cache[n];
}

// ===== 0/1 knapsack: a real DP ==============================================
// Items have weight & value; pick a subset with total weight <= cap maximizing
// value. dp[i][w] = best value using the first i items within budget w.
static long knapsack(const int *weight, const int *value, int n, int cap) {
    // (n+1) x (cap+1) table, allocated flat and freed at the end.
    long *dp = calloc((size_t)(n + 1) * (size_t)(cap + 1), sizeof(long));
    if (!dp) { perror("calloc"); exit(1); }
    size_t stride = (size_t)(cap + 1);

    for (int i = 1; i <= n; i++) {
        for (int w = 0; w <= cap; w++) {
            long without = dp[(size_t)(i - 1) * stride + (size_t)w];
            long best = without;
            if (weight[i - 1] <= w) {
                long with = value[i - 1] +
                    dp[(size_t)(i - 1) * stride + (size_t)(w - weight[i - 1])];
                if (with > best) best = with;
            }
            dp[(size_t)i * stride + (size_t)w] = best;
        }
    }
    long answer = dp[(size_t)n * stride + (size_t)cap];
    free(dp);
    return answer;
}

int main(void) {
    printf("=== DP part 1: Fibonacci, naive recursion vs memoization ===\n\n");
    printf("%4s | %14s | %14s | %12s\n", "n", "naive calls", "memo calls", "fib(n)");
    printf("-----+----------------+----------------+-------------\n");

    int ns[] = {10, 20, 30, 35, 40};
    for (size_t i = 0; i < sizeof ns / sizeof *ns; i++) {
        int n = ns[i];
        g_naive_calls = 0;
        long r1 = fib_naive(n);

        long *cache = malloc((size_t)(n + 1) * sizeof(long));
        if (!cache) { perror("malloc"); exit(1); }
        for (int k = 0; k <= n; k++) cache[k] = -1;
        g_memo_calls = 0;
        long r2 = fib_memo(n, cache);
        free(cache);

        if (r1 != r2) { fprintf(stderr, "BUG: fib mismatch\n"); return 1; }
        printf("%4d | %14ld | %14ld | %12ld\n", n, g_naive_calls, g_memo_calls, r1);
    }
    printf("\nNaive calls explode ~exponentially; memo is linear in n. Same answer,\n");
    printf("astronomically less work — that is the whole point of DP.\n\n");

    printf("=== DP part 2: 0/1 knapsack ===\n");
    int weight[] = {1, 3, 4, 5};
    int value[]  = {1, 4, 5, 7};
    int n = (int)(sizeof weight / sizeof *weight);
    int cap = 7;
    printf("items (weight,value): ");
    for (int i = 0; i < n; i++) printf("(%d,%d) ", weight[i], value[i]);
    printf("\ncapacity = %d\n", cap);
    long best = knapsack(weight, value, n, cap);
    printf("max value achievable = %ld   (take items {3,4} : weight 3+4=7, value 4+5=9)\n",
           best);
    return 0;
}
