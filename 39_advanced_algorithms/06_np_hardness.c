// Module 39 — Demo 6: NP-hardness — Vertex Cover, brute force vs 2-approximation
//
// A VERTEX COVER of a graph is a set of vertices that touches (covers) every edge:
// for each edge, at least one endpoint is in the set. MINIMUM vertex cover asks for the
// smallest such set. The DECISION version ("is there a cover of size <= k?") is
// NP-complete: we know no polynomial-time algorithm, and if one existed, every problem
// in NP would be solvable in polynomial time (P = NP). See README §6 for P vs NP,
// reductions, and what "approximation" honestly buys you.
//
// Here we do two things on the same small graphs and compare:
//   (1) BRUTE FORCE: try every subset of vertices (2^n of them), keep the smallest
//       that covers all edges. Correct, but exponential -- only feasible for tiny n.
//   (2) 2-APPROXIMATION: repeatedly pick any uncovered edge and add BOTH its endpoints
//       to the cover. Runs in O(E). It never returns more than 2x the optimum, because
//       the edges we pick share no vertex (a "matching"); any cover must use >= 1
//       endpoint per picked edge, so OPT >= (#picked edges) and we used exactly 2x that.
//
// We print approx size vs optimal size for several graphs; approx <= 2 * optimal always.
// Build & run with: make run6.  Read alongside README.md §6.

#include <stdio.h>
#include <stdlib.h>

typedef struct { int u, v; } EdgeUV;

typedef struct {
    int n;            // vertices 0..n-1
    int m;            // edge count
    EdgeUV *edges;
} GraphUV;

// --- Brute force: smallest subset (bitmask over vertices) covering every edge. -----
static int brute_force_vc(const GraphUV *g) {
    int best = g->n;                       // taking all vertices always covers
    for (unsigned mask = 0; mask < (1u << g->n); mask++) {
        // does this subset cover all edges?
        int covers = 1;
        for (int e = 0; e < g->m; e++) {
            int in_u = (mask >> g->edges[e].u) & 1u;
            int in_v = (mask >> g->edges[e].v) & 1u;
            if (!in_u && !in_v) { covers = 0; break; }
        }
        if (!covers) continue;
        // popcount of mask
        int size = 0;
        for (unsigned b = mask; b; b &= b - 1) size++;
        if (size < best) best = size;
    }
    return best;
}

// --- 2-approximation: pick uncovered edges, add both endpoints. --------------------
static int approx_vc(const GraphUV *g) {
    int *in_cover = calloc((size_t)g->n, sizeof *in_cover);
    int *covered  = calloc((size_t)g->m, sizeof *covered);
    int size = 0;

    for (int e = 0; e < g->m; e++) {
        if (covered[e]) continue;
        int u = g->edges[e].u, v = g->edges[e].v;
        // Add both endpoints of this still-uncovered edge.
        if (!in_cover[u]) { in_cover[u] = 1; size++; }
        if (!in_cover[v]) { in_cover[v] = 1; size++; }
        // Mark every edge now covered by u or v.
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
    printf("  %-10s n=%d m=%2d : optimal=%d  approx=%d  ratio=%.2f  (approx <= 2*opt? %s)\n",
           label, n, m, opt, apx, opt ? (double)apx / opt : 0.0,
           apx <= 2 * opt ? "yes" : "NO");
}

int main(void) {
    printf("=== Vertex Cover: exact (brute force, 2^n) vs 2-approximation (O(E)) ===\n\n");

    // Triangle: every pair connected. OPT = 2.
    EdgeUV tri[] = {{0,1},{1,2},{0,2}};
    run_case("triangle", 3, tri, 3);

    // Path 0-1-2-3-4. OPT = 2 (vertices 1 and 3).
    EdgeUV path[] = {{0,1},{1,2},{2,3},{3,4}};
    run_case("path-5", 5, path, 4);

    // Star: center 0 joined to 1,2,3,4. OPT = 1 (the center).
    EdgeUV star[] = {{0,1},{0,2},{0,3},{0,4}};
    run_case("star-5", 5, star, 4);

    // A denser 6-vertex graph.
    EdgeUV dense[] = {{0,1},{0,2},{1,2},{1,3},{2,4},{3,4},{3,5},{4,5}};
    run_case("dense-6", 6, dense, 8);

    printf("\n  The approximation is fast and provably within 2x, but is NOT exact:\n");
    printf("  for the triangle it can return 2 (=optimal) or, on other inputs, up to 2x.\n");
    printf("  No known polynomial algorithm gives the exact minimum for all graphs --\n");
    printf("  that is the practical meaning of NP-hardness. (See README for P vs NP.)\n");
    return 0;
}
