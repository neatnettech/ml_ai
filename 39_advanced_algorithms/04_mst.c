// Module 39 — Demo 4: Minimum Spanning Tree via Kruskal + union-find
//
// A spanning tree of a connected weighted graph picks n-1 edges that connect all n
// vertices with no cycle. The MINIMUM spanning tree minimizes total edge weight.
// Kruskal's algorithm: sort all edges by weight ascending, then walk them, adding an
// edge iff it joins two so-far-disconnected components (else it would make a cycle).
//
// The "are these two endpoints already connected?" test is exactly what a DISJOINT-SET
// (union-find) structure answers in near-constant time: find(x) returns the
// representative of x's component; union(a,b) merges two components. With union-by-rank
// + path compression, m operations cost O(m * alpha(n)) — alpha is the inverse-
// Ackermann function, effectively <= 4 for any n in the universe.
//
// Why is Kruskal correct? (Cut property, see README §4.) For any partition of the
// vertices into two sets, the cheapest edge crossing it is in SOME MST. Kruskal, taking
// edges cheapest-first and skipping cycle-makers, always adds such a safe crossing edge,
// so it builds an MST. Build & run with: make run4.  Read alongside README.md §4.

#include <stdio.h>
#include <stdlib.h>

// --- Disjoint-set (union-find) with union by rank + path compression --------------
typedef struct {
    int *parent;
    int *rank;
} DSU;

static DSU *dsu_new(int n) {
    DSU *d = malloc(sizeof *d);
    d->parent = malloc((size_t)n * sizeof *d->parent);
    d->rank   = calloc((size_t)n, sizeof *d->rank);
    for (int i = 0; i < n; i++) d->parent[i] = i;   // each element its own set
    return d;
}

static void dsu_free(DSU *d) { free(d->parent); free(d->rank); free(d); }

static int dsu_find(DSU *d, int x) {
    // Path compression: point every node on the way to root directly at the root.
    if (d->parent[x] != x) d->parent[x] = dsu_find(d, d->parent[x]);
    return d->parent[x];
}

// Returns 1 if a merge happened, 0 if a and b were already in the same set.
static int dsu_union(DSU *d, int a, int b) {
    int ra = dsu_find(d, a), rb = dsu_find(d, b);
    if (ra == rb) return 0;
    // Union by rank: hang the shorter tree under the taller to keep depth small.
    if (d->rank[ra] < d->rank[rb]) { int t = ra; ra = rb; rb = t; }
    d->parent[rb] = ra;
    if (d->rank[ra] == d->rank[rb]) d->rank[ra]++;
    return 1;
}

// --- Edges ------------------------------------------------------------------------
typedef struct { int u, v, w; } EdgeKW;

static int by_weight(const void *pa, const void *pb) {
    const EdgeKW *a = pa, *b = pb;
    return a->w - b->w;
}

int main(void) {
    const char *name = "ABCDEFG";
    int n = 7;
    EdgeKW edges[] = {
        {0, 1, 7}, {0, 3, 5},
        {1, 2, 8}, {1, 3, 9}, {1, 4, 7},
        {2, 4, 5},
        {3, 4, 15}, {3, 5, 6},
        {4, 5, 8}, {4, 6, 9},
        {5, 6, 11},
    };
    int m = (int)(sizeof edges / sizeof *edges);

    printf("=== Minimum Spanning Tree (Kruskal + union-find) ===\n\n");
    printf("  %d vertices (A..G), %d edges. Sort edges by weight, add if no cycle:\n\n", n, m);

    qsort(edges, (size_t)m, sizeof *edges, by_weight);

    DSU *d = dsu_new(n);
    int total = 0, picked = 0;
    for (int i = 0; i < m && picked < n - 1; i++) {
        // union returns nonzero only when the edge joins two distinct components.
        if (dsu_union(d, edges[i].u, edges[i].v)) {
            printf("    add %c-%c (w=%2d)\n", name[edges[i].u], name[edges[i].v], edges[i].w);
            total += edges[i].w;
            picked++;
        } else {
            printf("    skip %c-%c (w=%2d) -- would make a cycle\n",
                   name[edges[i].u], name[edges[i].v], edges[i].w);
        }
    }

    printf("\n  MST has %d edges, total weight = %d\n", picked, total);

    dsu_free(d);
    return 0;
}
