// SOLUTION 42.3 — Quorum read

#include <stdio.h>

int quorum_read(const int values[], int n, int R, int *out) {
    if (R <= 0 || R > n) return 0;          // can't form a quorum of R reads
    // Read the first R replicas; a quorum requires all R to agree.
    int first = values[0];
    for (int i = 1; i < R; i++) {
        if (values[i] != first) return 0;   // disagreement -> no quorum
    }
    *out = first;
    return 1;
}

int main(void) {
    int out;

    int a[] = {20, 20, 10};
    if (quorum_read(a, 3, 2, &out)) printf("A: R=2 over {20,20,10} -> quorum value = %d\n", out);
    else                            printf("A: R=2 over {20,20,10} -> no quorum\n");

    int b[] = {20, 10, 20};
    if (quorum_read(b, 3, 2, &out)) printf("B: R=2 over {20,10,20} -> quorum value = %d\n", out);
    else                            printf("B: R=2 over {20,10,20} -> no quorum\n");

    int c[] = {20, 20};
    if (quorum_read(c, 2, 3, &out)) printf("C: R=3 over 2 replicas -> quorum value = %d\n", out);
    else                            printf("C: R=3 over 2 replicas -> no quorum\n");
    return 0;
}
