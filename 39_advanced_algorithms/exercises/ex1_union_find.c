// Exercise 39.1 — Union-Find (disjoint-set)
//
// Implement `find` (with path compression) and `dsu_union` (union by rank). Then the
// driver below merges some elements and prints which ones share a set. With a correct
// implementation `make ex1` matches the expected output in README §7 (== `make sol1`).
// Solution in ../solutions/ex1_union_find.c.

#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int *parent;
    int *rank;
} DSU;

static DSU *dsu_new(int n) {
    DSU *d = malloc(sizeof *d);
    d->parent = malloc((size_t)n * sizeof *d->parent);
    d->rank   = calloc((size_t)n, sizeof *d->rank);
    for (int i = 0; i < n; i++) d->parent[i] = i;
    return d;
}

static void dsu_free(DSU *d) { free(d->parent); free(d->rank); free(d); }

// TODO: return the representative (root) of x's set, compressing the path on the way.
//   Hint: if parent[x] != x, set parent[x] = dsu_find(d, parent[x]); then return it.
static int dsu_find(DSU *d, int x) {
    (void)d;          // remove once you use d
    return x;         // TODO: replace with the real find
}

// TODO: merge the sets of a and b. Return 1 if they were separate (a merge happened),
//   0 if they were already together. Use union by rank: attach the lower-rank root
//   under the higher-rank root; if ranks tie, pick one and increment its rank.
static int dsu_union(DSU *d, int a, int b) {
    (void)d; (void)a; (void)b;   // remove once you use them
    return 0;                     // TODO: replace with the real union
}

int main(void) {
    int n = 7;
    DSU *d = dsu_new(n);

    // Merge: {0,1}, {1,2}, {3,4}, {5,6}.  Expected components: {0,1,2} {3,4} {5,6}.
    dsu_union(d, 0, 1);
    dsu_union(d, 1, 2);
    dsu_union(d, 3, 4);
    dsu_union(d, 5, 6);

    printf("connected(0,2) = %d  (expect 1)\n", dsu_find(d, 0) == dsu_find(d, 2));
    printf("connected(0,3) = %d  (expect 0)\n", dsu_find(d, 0) == dsu_find(d, 3));
    printf("connected(3,4) = %d  (expect 1)\n", dsu_find(d, 3) == dsu_find(d, 4));
    printf("connected(4,5) = %d  (expect 0)\n", dsu_find(d, 4) == dsu_find(d, 5));

    int comps = 0;
    for (int i = 0; i < n; i++) if (dsu_find(d, i) == i) comps++;
    printf("number of components = %d  (expect 3)\n", comps);

    dsu_free(d);
    return 0;
}
