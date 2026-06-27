// Exercise 39.2 — Dijkstra (the relaxation core)
//
// Fill in `dijkstra` for the small graph given as an adjacency matrix (W[u][v] = weight
// of edge u->v, or 0 for "no edge"). Use the simple O(V^2) version: repeatedly pick the
// unvisited vertex with the smallest tentative distance, mark it visited, and RELAX all
// its outgoing edges. With a correct implementation `make ex2` matches README §7
// (== `make sol2`). Solution in ../solutions/ex2_dijkstra.c.

#include <stdio.h>
#include <limits.h>

#define N 6
#define INF INT_MAX

// Directed weighted graph, vertices A..F (0..5). 0 means "no edge".
static const int W[N][N] = {
    /*    A   B   C   D   E   F */
    /*A*/{ 0,  7,  9,  0,  0, 14},
    /*B*/{ 0,  0, 10, 15,  0,  0},
    /*C*/{ 0,  0,  0, 11,  0,  2},
    /*D*/{ 0,  0,  0,  0,  6,  0},
    /*E*/{ 0,  0,  0,  0,  0,  0},
    /*F*/{ 0,  0,  0,  0,  9,  0},
};

static void dijkstra(int src, int dist[N]) {
    int visited[N];
    for (int v = 0; v < N; v++) { dist[v] = INF; visited[v] = 0; }
    dist[src] = 0;

    for (int iter = 0; iter < N; iter++) {
        // TODO 1: among unvisited vertices, find u with the smallest dist[u].
        //         If none is reachable (all remaining are INF), break.
        int u = -1;
        // ... your code: set u to the best unvisited vertex, or leave -1 if none ...

        if (u == -1) break;
        visited[u] = 1;

        // TODO 2: relax every outgoing edge of u.
        //   for each v with W[u][v] != 0:
        //       if dist[u] + W[u][v] < dist[v]  then  dist[v] = dist[u] + W[u][v];
        //   (guard against INF + weight overflowing — only relax when dist[u] != INF.)
        (void)u; (void)W;   // remove these once you implement the relaxation
    }
}

int main(void) {
    const char *name = "ABCDEF";
    int dist[N];
    dijkstra(0, dist);   // from A

    printf("shortest distances from A:\n");
    for (int v = 0; v < N; v++) {
        if (dist[v] == INF) printf("  A -> %c : unreachable\n", name[v]);
        else                printf("  A -> %c : %d\n", name[v], dist[v]);
    }
    // Expected: A0 B7 C9 D20 E20 F11
    return 0;
}
