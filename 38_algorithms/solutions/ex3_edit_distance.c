// SOLUTION 38.3 — Edit (Levenshtein) distance via DP

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int min3(int x, int y, int z) {
    int m = x < y ? x : y;
    return m < z ? m : z;
}

static int edit_distance(const char *a, const char *b) {
    int la = (int)strlen(a), lb = (int)strlen(b);
    int *dp = malloc((size_t)(la + 1) * (size_t)(lb + 1) * sizeof(int));
    if (!dp) { perror("malloc"); exit(1); }
    size_t stride = (size_t)(lb + 1);

    for (int i = 0; i <= la; i++) dp[(size_t)i * stride + 0] = i;
    for (int j = 0; j <= lb; j++) dp[0 * stride + (size_t)j] = j;

    for (int i = 1; i <= la; i++) {
        for (int j = 1; j <= lb; j++) {
            int cost = (a[i - 1] == b[j - 1]) ? 0 : 1;
            dp[(size_t)i * stride + (size_t)j] = min3(
                dp[(size_t)(i - 1) * stride + (size_t)j] + 1,        // delete
                dp[(size_t)i * stride + (size_t)(j - 1)] + 1,        // insert
                dp[(size_t)(i - 1) * stride + (size_t)(j - 1)] + cost); // sub/match
        }
    }

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
