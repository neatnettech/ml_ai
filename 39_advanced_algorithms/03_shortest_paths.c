// Module 39 — Demo 3: Dijkstra's shortest paths with a binary-heap priority queue
//
// Given a weighted graph with NON-NEGATIVE edge weights and a source s, Dijkstra finds
// the shortest distance from s to every other vertex. The idea: keep a tentative
// distance dist[v] to each vertex; repeatedly pull the unsettled vertex with the
// SMALLEST tentative distance, declare it settled (its distance is now final), and
// "relax" its outgoing edges — dist[w] = min(dist[w], dist[u] + weight(u,w)).
//
// Why is the pulled vertex's distance final? (See README §3.) When we extract u with
// the minimum tentative distance, any other path to u must leave the settled set at
// some vertex x with dist[x] >= dist[u], then travel a non-negative remainder — so it
// cannot beat dist[u]. Non-negativity is essential; with negative edges this fails and
// you need Bellman-Ford (O(V*E), also detects negative cycles).
//
// The priority queue is a binary min-heap, giving O((V+E) log V). Build & run: make run3.
// Read alongside README.md §3.

#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

#define INF INT_MAX

// --- Graph as adjacency list ------------------------------------------------------
typedef struct Edge {
    int to;
    int weight;
    struct Edge *next;
} Edge;

typedef struct {
    int n;
    Edge **adj;     // adj[v] = head of edge list for vertex v
} Graph;

static Graph *graph_new(int n) {
    Graph *g = malloc(sizeof *g);
    g->n = n;
    g->adj = calloc((size_t)n, sizeof *g->adj);
    return g;
}

static void graph_add_edge(Graph *g, int u, int v, int w) {
    Edge *e = malloc(sizeof *e);
    e->to = v; e->weight = w; e->next = g->adj[u];
    g->adj[u] = e;
}

static void graph_free(Graph *g) {
    for (int v = 0; v < g->n; v++) {
        Edge *e = g->adj[v];
        while (e) { Edge *nx = e->next; free(e); e = nx; }
    }
    free(g->adj);
    free(g);
}

// --- Binary min-heap keyed by distance, storing (vertex, dist) pairs --------------
// We also keep pos[v] = index of vertex v in the heap (or -1) for decrease-key.
typedef struct {
    int  *vtx;   // heap[i] -> vertex
    int  *key;   // heap[i] -> its distance key
    int  *pos;   // pos[vertex] -> i in heap, or -1
    int   size;
} Heap;

static Heap *heap_new(int n) {
    Heap *h = malloc(sizeof *h);
    h->vtx = malloc((size_t)n * sizeof *h->vtx);
    h->key = malloc((size_t)n * sizeof *h->key);
    h->pos = malloc((size_t)n * sizeof *h->pos);
    for (int i = 0; i < n; i++) h->pos[i] = -1;
    h->size = 0;
    return h;
}

static void heap_free(Heap *h) {
    free(h->vtx); free(h->key); free(h->pos); free(h);
}

static void heap_swap(Heap *h, int i, int j) {
    int tv = h->vtx[i]; h->vtx[i] = h->vtx[j]; h->vtx[j] = tv;
    int tk = h->key[i]; h->key[i] = h->key[j]; h->key[j] = tk;
    h->pos[h->vtx[i]] = i;
    h->pos[h->vtx[j]] = j;
}

static void heap_up(Heap *h, int i) {
    while (i > 0) {
        int parent = (i - 1) / 2;
        if (h->key[parent] <= h->key[i]) break;
        heap_swap(h, i, parent);
        i = parent;
    }
}

static void heap_down(Heap *h, int i) {
    for (;;) {
        int l = 2 * i + 1, r = 2 * i + 2, smallest = i;
        if (l < h->size && h->key[l] < h->key[smallest]) smallest = l;
        if (r < h->size && h->key[r] < h->key[smallest]) smallest = r;
        if (smallest == i) break;
        heap_swap(h, i, smallest);
        i = smallest;
    }
}

static void heap_push(Heap *h, int vertex, int key) {
    int i = h->size++;
    h->vtx[i] = vertex; h->key[i] = key; h->pos[vertex] = i;
    heap_up(h, i);
}

// Lower the key of a vertex already in the heap (the "decrease-key" operation).
static void heap_decrease(Heap *h, int vertex, int key) {
    int i = h->pos[vertex];
    h->key[i] = key;
    heap_up(h, i);
}

static int heap_pop_min(Heap *h) {
    int top = h->vtx[0];
    h->pos[top] = -1;
    h->size--;
    if (h->size > 0) {
        h->vtx[0] = h->vtx[h->size];
        h->key[0] = h->key[h->size];
        h->pos[h->vtx[0]] = 0;
        heap_down(h, 0);
    }
    return top;
}

// --- Dijkstra ---------------------------------------------------------------------
static void dijkstra(Graph *g, int src, int *dist) {
    for (int v = 0; v < g->n; v++) dist[v] = INF;
    dist[src] = 0;

    Heap *h = heap_new(g->n);
    heap_push(h, src, 0);

    while (h->size > 0) {
        int u = heap_pop_min(h);      // u's distance is now final
        for (Edge *e = g->adj[u]; e; e = e->next) {
            // Relaxation: can we reach e->to faster by going through u?
            long nd = (long)dist[u] + e->weight;
            if (nd < dist[e->to]) {
                dist[e->to] = (int)nd;
                if (h->pos[e->to] == -1) heap_push(h, e->to, dist[e->to]);
                else                     heap_decrease(h, e->to, dist[e->to]);
            }
        }
    }
    heap_free(h);
}

int main(void) {
    // A small directed weighted graph, 6 vertices labelled A..F (0..5).
    const char *name = "ABCDEF";
    int n = 6;
    Graph *g = graph_new(n);
    graph_add_edge(g, 0, 1, 7);   // A->B
    graph_add_edge(g, 0, 2, 9);   // A->C
    graph_add_edge(g, 0, 5, 14);  // A->F
    graph_add_edge(g, 1, 2, 10);  // B->C
    graph_add_edge(g, 1, 3, 15);  // B->D
    graph_add_edge(g, 2, 3, 11);  // C->D
    graph_add_edge(g, 2, 5, 2);   // C->F
    graph_add_edge(g, 3, 4, 6);   // D->E
    graph_add_edge(g, 5, 4, 9);   // F->E

    printf("=== Dijkstra's shortest paths from A (non-negative weights) ===\n\n");
    printf("  edges: A-B7 A-C9 A-F14 B-C10 B-D15 C-D11 C-F2 D-E6 F-E9 (directed)\n\n");

    int *dist = malloc((size_t)n * sizeof *dist);
    dijkstra(g, 0, dist);

    printf("  shortest distance from A to each vertex:\n");
    for (int v = 0; v < n; v++) {
        if (dist[v] == INF) printf("    A -> %c : unreachable\n", name[v]);
        else                printf("    A -> %c : %d\n", name[v], dist[v]);
    }

    printf("\n  Note: with NEGATIVE edge weights Dijkstra can be wrong; use Bellman-Ford\n");
    printf("  (O(V*E)), which also detects negative cycles.\n");

    free(dist);
    graph_free(g);
    return 0;
}
