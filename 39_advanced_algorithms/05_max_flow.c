// Module 39 — Demo 5: Maximum flow via Edmonds-Karp (BFS-augmenting Ford-Fulkerson)
//
// A flow network is a directed graph with a CAPACITY on each edge, a source s, and a
// sink t. A flow ships units from s to t without exceeding any capacity and conserving
// flow at every other node (in = out). Max-flow asks: how many units can we push?
//
// Ford-Fulkerson: repeatedly find an "augmenting path" from s to t in the RESIDUAL
// graph (remaining capacity, plus back-edges that let us cancel earlier flow), and push
// the path's bottleneck along it. Edmonds-Karp picks the augmenting path by BFS
// (fewest edges), which bounds the work at O(V * E^2) and always terminates.
//
// Max-flow min-cut theorem (README §5): the maximum flow value EQUALS the minimum
// capacity of any s-t cut (a way to split the vertices with s on one side, t on the
// other; the cut's capacity is the total capacity of edges crossing forward). When BFS
// can no longer reach t in the residual graph, the vertices still reachable from s form
// exactly the min cut, and the flow we have is maximal. Build & run: make run5.
// Read alongside README.md §5.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define INF 1000000000

static int n;            // number of vertices
static int *cap;         // cap[u*n + v] = residual capacity u->v

static int cap_at(int u, int v) { return cap[u * n + v]; }

// BFS for a shortest augmenting path; fills parent[] and returns bottleneck (0 if none).
static int bfs(int s, int t, int *parent) {
    for (int i = 0; i < n; i++) parent[i] = -1;
    parent[s] = s;
    int *queue = malloc((size_t)n * sizeof *queue);
    int head = 0, tail = 0;
    queue[tail++] = s;

    while (head < tail) {
        int u = queue[head++];
        for (int v = 0; v < n; v++) {
            if (parent[v] == -1 && cap_at(u, v) > 0) {
                parent[v] = u;
                if (v == t) { free(queue); goto found; }
                queue[tail++] = v;
            }
        }
    }
    free(queue);
    return 0;   // t not reachable: no augmenting path

found:;
    // Walk back from t to s to find the bottleneck (min residual along the path).
    int bottleneck = INF;
    for (int v = t; v != s; v = parent[v]) {
        int u = parent[v];
        if (cap_at(u, v) < bottleneck) bottleneck = cap_at(u, v);
    }
    return bottleneck;
}

static int edmonds_karp(int s, int t) {
    int max_flow = 0;
    int *parent = malloc((size_t)n * sizeof *parent);
    int bottleneck;
    while ((bottleneck = bfs(s, t, parent)) > 0) {
        // Push `bottleneck` along the path: subtract on forward edges, add to back edges.
        for (int v = t; v != s; v = parent[v]) {
            int u = parent[v];
            cap[u * n + v] -= bottleneck;
            cap[v * n + u] += bottleneck;   // residual back-edge allows undoing flow
        }
        max_flow += bottleneck;
        printf("    augmenting path found, pushed %d unit(s)  (total %d)\n",
               bottleneck, max_flow);
    }
    free(parent);
    return max_flow;
}

int main(void) {
    // Classic CLRS-style network: 6 vertices, s=0, t=5.
    n = 6;
    int s = 0, t = 5;
    const char *name = "S1234T";
    cap = calloc((size_t)(n * n), sizeof *cap);

    // directed capacities
    cap[0 * n + 1] = 16; cap[0 * n + 2] = 13;
    cap[1 * n + 3] = 12;
    cap[2 * n + 1] = 4;  cap[2 * n + 4] = 14;
    cap[3 * n + 2] = 9;  cap[3 * n + 5] = 20;
    cap[4 * n + 3] = 7;  cap[4 * n + 5] = 4;

    printf("=== Maximum flow (Edmonds-Karp) from S to T ===\n\n");
    printf("  network capacities: S->1:16 S->2:13 1->3:12 2->1:4 2->4:14\n");
    printf("                      3->2:9 3->T:20 4->3:7 4->T:4\n\n");

    int flow = edmonds_karp(s, t);

    printf("\n  MAX FLOW value = %d\n", flow);

    // Show the min cut: vertices still reachable from s in the final residual graph.
    int *parent = malloc((size_t)n * sizeof *parent);
    bfs(s, t, parent);   // t unreachable now; parent[v]!=-1 marks the source side
    printf("  min cut: source side = {");
    int first = 1;
    for (int v = 0; v < n; v++) {
        if (parent[v] != -1) { printf("%s%c", first ? "" : ",", name[v]); first = 0; }
    }
    printf("}  (its capacity equals the max flow, by max-flow min-cut)\n");

    free(parent);
    free(cap);
    return 0;
}
