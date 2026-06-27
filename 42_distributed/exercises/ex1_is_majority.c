// Exercise 42.1 — Majority / quorum check
//
// Consensus (Demo 4) hinges on one tiny predicate: did a candidate get a MAJORITY of
// votes? Implement `is_majority(votes, n)` so it returns 1 iff `votes` is strictly
// more than half of `n` (i.e. votes > n/2). Then the election tally below should match
// the expected output in README.md §5. Solution in ../solutions/ex1_is_majority.c.

#include <stdio.h>

int is_majority(int votes, int n) {
    // TODO: return 1 if `votes` is a strict majority of `n`, else 0.
    // A majority is MORE than half: for n=5 you need 3; for n=4 you need 3; for n=3, 2.
    // Hint: votes > n/2  works for both odd and even n with integer division.
    (void)votes; (void)n;   // remove this line once you use them
    return 0;
}

int main(void) {
    // (votes, n) cases spanning odd/even cluster sizes and the boundary.
    int cases[][2] = {{3,5},{2,5},{3,4},{2,4},{2,3},{1,3},{1,1}};
    int ncases = (int)(sizeof cases / sizeof *cases);
    for (int i = 0; i < ncases; i++) {
        int v = cases[i][0], n = cases[i][1];
        printf("is_majority(votes=%d, n=%d) = %d\n", v, n, is_majority(v, n));
    }

    // Use it in an election tally: count YES votes, then decide.
    int ballots[] = {1, 1, 0, 1, 0};   // 1 = voted for our candidate, 0 = did not
    int n = (int)(sizeof ballots / sizeof *ballots);
    int yes = 0;
    for (int i = 0; i < n; i++) yes += ballots[i];
    printf("\ntally: %d/%d YES -> %s\n", yes, n,
           is_majority(yes, n) ? "ELECTED (majority)" : "no majority");
    return 0;
}
