// SOLUTION 39.1 — Union-Find (disjoint-set)

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

static int dsu_find(DSU *d, int x) {
    if (d->parent[x] != x) d->parent[x] = dsu_find(d, d->parent[x]);   // path compression
    return d->parent[x];
}

static int dsu_union(DSU *d, int a, int b) {
    int ra = dsu_find(d, a), rb = dsu_find(d, b);
    if (ra == rb) return 0;
    if (d->rank[ra] < d->rank[rb]) { int t = ra; ra = rb; rb = t; }    // union by rank
    d->parent[rb] = ra;
    if (d->rank[ra] == d->rank[rb]) d->rank[ra]++;
    return 1;
}

int main(void) {
    int n = 7;
    DSU *d = dsu_new(n);

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
