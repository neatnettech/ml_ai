// SOLUTION 39.2 — Dijkstra (the relaxation core)

#include <stdio.h>
#include <limits.h>

#define N 6
#define INF INT_MAX

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
        // Pick the unvisited vertex with the smallest tentative distance.
        int u = -1;
        int best = INF;
        for (int v = 0; v < N; v++) {
            if (!visited[v] && dist[v] < best) { best = dist[v]; u = v; }
        }
        if (u == -1) break;     // remaining vertices are unreachable
        visited[u] = 1;

        // Relax every outgoing edge of u.
        if (dist[u] != INF) {
            for (int v = 0; v < N; v++) {
                if (W[u][v] != 0 && dist[u] + W[u][v] < dist[v]) {
                    dist[v] = dist[u] + W[u][v];
                }
            }
        }
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
    return 0;
}
