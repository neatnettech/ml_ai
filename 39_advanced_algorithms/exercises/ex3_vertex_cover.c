// Exercise 39.3 — Vertex Cover 2-approximation
//
// The brute-force optimum is provided below. Implement `approx_vc`: repeatedly take any
// still-uncovered edge, add BOTH its endpoints to the cover, and mark every edge those
// endpoints cover. Return the cover size. The driver then checks, on several small
// graphs, that your approximation is at most 2x the exact optimum. With a correct
// implementation `make ex3` matches README §7 (== `make sol3`).
// Solution in ../solutions/ex3_vertex_cover.c.

#include <stdio.h>
#include <stdlib.h>

typedef struct { int u, v; } EdgeUV;
typedef struct { int n, m; EdgeUV *edges; } GraphUV;

// Exact minimum vertex cover by trying all 2^n subsets (small n only).
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

// TODO: implement the 2-approximation.
//   - keep a per-vertex "in_cover" flag and a per-edge "covered" flag (calloc them)
//   - for each edge e not yet covered:
//       add endpoints u and v to the cover (count each only once)
//       mark every edge touching u or v as covered
//   - return the number of vertices added; free your scratch arrays.
static int approx_vc(const GraphUV *g) {
    (void)g;     // remove once you use g
    return 0;    // TODO: replace with the real 2-approximation
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
