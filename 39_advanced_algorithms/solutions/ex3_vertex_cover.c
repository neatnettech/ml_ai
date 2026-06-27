// SOLUTION 39.3 — Vertex Cover 2-approximation

#include <stdio.h>
#include <stdlib.h>

typedef struct { int u, v; } EdgeUV;
typedef struct { int n, m; EdgeUV *edges; } GraphUV;

static int brute_force_vc(const GraphUV *g) {
    int best = g->n;
    for (unsigned mask = 0; mask < (1u << g->n); mask++) {
        int covers = 1;
        for (int e = 0; e < g->m; e++) {
            int in_u = (mask >> g->edges[e].u) & 1u;
            int in_v = (mask >> g->edges[e].v) & 1u;
            if (!in_u && !in_v) { covers = 0; break; }
        }
        if (!covers) continue;
        int size = 0;
        for (unsigned b = mask; b; b &= b - 1) size++;
        if (size < best) best = size;
    }
    return best;
}

static int approx_vc(const GraphUV *g) {
    int *in_cover = calloc((size_t)g->n, sizeof *in_cover);
    int *covered  = calloc((size_t)g->m, sizeof *covered);
    int size = 0;

    for (int e = 0; e < g->m; e++) {
        if (covered[e]) continue;
        int u = g->edges[e].u, v = g->edges[e].v;
        if (!in_cover[u]) { in_cover[u] = 1; size++; }
        if (!in_cover[v]) { in_cover[v] = 1; size++; }
        for (int f = 0; f < g->m; f++) {
            if (g->edges[f].u == u || g->edges[f].v == u ||
                g->edges[f].u == v || g->edges[f].v == v)
                covered[f] = 1;
        }
    }

    free(in_cover);
    free(covered);
    return size;
}

static void run_case(const char *label, int n, EdgeUV *edges, int m) {
    GraphUV g = { n, m, edges };
    int opt = brute_force_vc(&g);
    int apx = approx_vc(&g);
    printf("  %-9s optimal=%d approx=%d  (approx <= 2*opt? %s)\n",
           label, opt, apx, apx <= 2 * opt ? "yes" : "NO");
}

int main(void) {
    EdgeUV tri[]   = {{0,1},{1,2},{0,2}};
    EdgeUV path[]  = {{0,1},{1,2},{2,3},{3,4}};
    EdgeUV star[]  = {{0,1},{0,2},{0,3},{0,4}};
    EdgeUV dense[] = {{0,1},{0,2},{1,2},{1,3},{2,4},{3,4},{3,5},{4,5}};

    printf("vertex cover: approx vs exact (approx must be <= 2 * optimal)\n");
    run_case("triangle", 3, tri,   3);
    run_case("path-5",   5, path,  4);
    run_case("star-5",   5, star,  4);
    run_case("dense-6",  6, dense, 8);
    return 0;
}
