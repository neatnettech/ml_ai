// SOLUTION 42.1 — Majority / quorum check

#include <stdio.h>

int is_majority(int votes, int n) {
    return votes > n / 2;   // strict majority: more than half
}

int main(void) {
    int cases[][2] = {{3,5},{2,5},{3,4},{2,4},{2,3},{1,3},{1,1}};
    int ncases = (int)(sizeof cases / sizeof *cases);
    for (int i = 0; i < ncases; i++) {
        int v = cases[i][0], n = cases[i][1];
        printf("is_majority(votes=%d, n=%d) = %d\n", v, n, is_majority(v, n));
    }

    int ballots[] = {1, 1, 0, 1, 0};
    int n = (int)(sizeof ballots / sizeof *ballots);
    int yes = 0;
    for (int i = 0; i < n; i++) yes += ballots[i];
    printf("\ntally: %d/%d YES -> %s\n", yes, n,
           is_majority(yes, n) ? "ELECTED (majority)" : "no majority");
    return 0;
}
