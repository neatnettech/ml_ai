// Exercise 42.3 — Quorum read
//
// Implement `quorum_read` (Demo 3): read R replicas and return the value once R of
// them AGREE on the same value; if no value appears on at least R replicas, report
// "no quorum". Match the expected output in README.md §5.
// Solution in ../solutions/ex3_quorum_read.c.
//
// Signature: read the first R entries of `values` (length n). If some value occurs at
// least R times among those R reads, set *out to that value and return 1; else return 0.
// (Reading exactly R replicas, a quorum means all R returned the SAME value.)

#include <stdio.h>

int quorum_read(const int values[], int n, int R, int *out) {
    // TODO:
    //   - guard: if R > n or R <= 0, there can be no quorum -> return 0.
    //   - look at the first R replicas (values[0..R-1]); if they all hold the same
    //     value, set *out to it and return 1; otherwise return 0 (no quorum).
    (void)values; (void)n; (void)R; (void)out;
    return 0;
}

int main(void) {
    int out;

    // Case A: 3 replicas, R=2, both read replicas agree on 20 -> quorum, value 20.
    int a[] = {20, 20, 10};
    if (quorum_read(a, 3, 2, &out)) printf("A: R=2 over {20,20,10} -> quorum value = %d\n", out);
    else                            printf("A: R=2 over {20,20,10} -> no quorum\n");

    // Case B: 3 replicas, R=2, the two read replicas disagree -> no quorum.
    int b[] = {20, 10, 20};
    if (quorum_read(b, 3, 2, &out)) printf("B: R=2 over {20,10,20} -> quorum value = %d\n", out);
    else                            printf("B: R=2 over {20,10,20} -> no quorum\n");

    // Case C: R larger than available replicas -> no quorum.
    int c[] = {20, 20};
    if (quorum_read(c, 2, 3, &out)) printf("C: R=3 over 2 replicas -> quorum value = %d\n", out);
    else                            printf("C: R=3 over 2 replicas -> no quorum\n");
    return 0;
}
