// Exercise 38.3 — Edit (Levenshtein) distance via DP
//
// The edit distance between two strings is the minimum number of single-character
// insertions, deletions, or substitutions to turn one into the other. It's a
// classic DP: dp[i][j] = distance between the first i chars of `a` and first j of
// `b`. Implement `edit_distance`. Then `make ex3` should match `make sol3`.
// Solution in ../solutions/ex3_edit_distance.c.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int min3(int x, int y, int z) {
    int m = x < y ? x : y;
    return m < z ? m : z;
}

// Return the Levenshtein distance between a and b.
static int edit_distance(const char *a, const char *b) {
    int la = (int)strlen(a), lb = (int)strlen(b);
    // (la+1) x (lb+1) table, flat. Free it before returning.
    int *dp = malloc((size_t)(la + 1) * (size_t)(lb + 1) * sizeof(int));
    if (!dp) { perror("malloc"); exit(1); }
    size_t stride = (size_t)(lb + 1);
    (void)min3;   // remove once you call it below

    // TODO: fill the table.
    //  base cases: dp[i][0] = i (delete i chars), dp[0][j] = j (insert j chars)
    //  recurrence for i>=1, j>=1:
    //     cost = (a[i-1] == b[j-1]) ? 0 : 1
    //     dp[i][j] = min3( dp[i-1][j] + 1,        // delete
    //                      dp[i][j-1] + 1,        // insert
    //                      dp[i-1][j-1] + cost )  // substitute/match
    //  Index dp as dp[(size_t)i * stride + (size_t)j].
    (void)stride;

    int answer = dp[(size_t)la * stride + (size_t)lb];
    free(dp);
    return answer;
}

int main(void) {
    struct { const char *a, *b; int expected; } cases[] = {
        {"kitten", "sitting", 3},
        {"flaw",   "lawn",    2},
        {"",       "abc",     3},
        {"same",   "same",    0},
        {"sunday", "saturday", 3},
    };
    for (size_t i = 0; i < sizeof cases / sizeof *cases; i++) {
        int d = edit_distance(cases[i].a, cases[i].b);
        printf("edit(\"%s\", \"%s\") = %d  (expected %d) %s\n",
               cases[i].a, cases[i].b, d, cases[i].expected,
               d == cases[i].expected ? "OK" : "WRONG");
    }
    return 0;
}
