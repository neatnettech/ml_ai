// Module 38 — Demo 5: Graphs — adjacency list, BFS and DFS
//
// A graph is vertices + edges. We store it as an ADJACENCY LIST: each vertex owns
// a linked list of its neighbours. Then two traversals:
//   - BFS (breadth-first) uses a QUEUE and visits nearest-first (level by level).
//   - DFS (depth-first) uses recursion/a stack and plunges down one path first.
// Both are O(V + E). Build & run with: make run5
//
// Read top to bottom alongside README.md §5.

#include <stdio.h>
#include <stdlib.h>

typedef struct AdjNode {
    int to;
    struct AdjNode *next;
} AdjNode;

typedef struct {
    AdjNode **adj;       // adj[v] = head of v's neighbour list
    size_t n;            // number of vertices
} Graph;

static Graph *graph_create(size_t n) {
    Graph *g = malloc(sizeof(*g));
    if (!g) { perror("malloc"); exit(1); }
    g->adj = calloc(n, sizeof(AdjNode *));
    if (!g->adj) { perror("calloc"); exit(1); }
    g->n = n;
    return g;
}

// Add a directed edge u->v at the front of u's list.
static void add_directed(Graph *g, int u, int v) {
    AdjNode *node = malloc(sizeof(*node));
    if (!node) { perror("malloc"); exit(1); }
    node->to = v;
    node->next = g->adj[u];
    g->adj[u] = node;
}

// Undirected edge = two directed edges. Front-insertion means a vertex's most
// recently added neighbour is visited first, so traversal order reflects that.
static void add_edge(Graph *g, int u, int v) {
    add_directed(g, u, v);
    add_directed(g, v, u);
}

static void graph_free(Graph *g) {
    for (size_t i = 0; i < g->n; i++) {
        AdjNode *e = g->adj[i];
        while (e) { AdjNode *nx = e->next; free(e); e = nx; }
    }
    free(g->adj);
    free(g);
}

// BFS from `start`: a simple ring-free array queue, visit nearest vertices first.
static void bfs(const Graph *g, int start) {
    int *visited = calloc(g->n, sizeof(int));
    int *queue = malloc(g->n * sizeof(int));
    if (!visited || !queue) { perror("alloc"); exit(1); }
    size_t head = 0, tail = 0;

    visited[start] = 1;
    queue[tail++] = start;
    printf("BFS from %d: ", start);
    while (head < tail) {
        int u = queue[head++];
        printf("%d ", u);
        for (AdjNode *e = g->adj[u]; e; e = e->next) {
            if (!visited[e->to]) { visited[e->to] = 1; queue[tail++] = e->to; }
        }
    }
    printf("\n");
    free(visited);
    free(queue);
}

// DFS via recursion. `visited` is shared across the recursive calls.
static void dfs_visit(const Graph *g, int u, int *visited) {
    visited[u] = 1;
    printf("%d ", u);
    for (AdjNode *e = g->adj[u]; e; e = e->next) {
        if (!visited[e->to]) dfs_visit(g, e->to, visited);
    }
}

static void dfs(const Graph *g, int start) {
    int *visited = calloc(g->n, sizeof(int));
    if (!visited) { perror("calloc"); exit(1); }
    printf("DFS from %d: ", start);
    dfs_visit(g, start, visited);
    printf("\n");
    free(visited);
}

int main(void) {
    // An undirected graph of 7 vertices (0..6):
    //
    //        0
    //       / \
    //      1   2
    //     / \   \
    //    3   4   5
    //         \ /
    //          6
    printf("=== Graph traversal (adjacency list) ===\n");
    Graph *g = graph_create(7);
    add_edge(g, 0, 1);
    add_edge(g, 0, 2);
    add_edge(g, 1, 3);
    add_edge(g, 1, 4);
    add_edge(g, 2, 5);
    add_edge(g, 4, 6);
    add_edge(g, 5, 6);

    printf("vertices: 0..6, undirected edges as drawn in the source comment.\n\n");
    bfs(g, 0);   // nearest-first: 0, then its neighbours, then theirs, ...
    dfs(g, 0);   // plunges deep along one branch before backing up

    graph_free(g);
    return 0;
}
