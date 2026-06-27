// Module 38 — Demo 4: Binary search tree + binary heap (priority queue)
//
// Two workhorse structures:
//   - A BINARY SEARCH TREE keeps keys ordered: left < node < right. An in-order
//     walk yields them sorted, and lookup/insert are O(h) (O(log n) when balanced).
//   - A BINARY HEAP (array-backed) is a complete tree where each parent <= its
//     children. push and pop-min are O(log n) — the basis of a priority queue.
// Build & run with: make run4
//
// Read top to bottom alongside README.md §4.

#include <stdio.h>
#include <stdlib.h>

// ===== Binary search tree ===================================================
typedef struct Node {
    int key;
    struct Node *left, *right;
} Node;

static Node *bst_insert(Node *root, int key) {
    if (!root) {
        Node *n = malloc(sizeof(*n));
        if (!n) { perror("malloc"); exit(1); }
        n->key = key; n->left = n->right = NULL;
        return n;
    }
    if (key < root->key)      root->left  = bst_insert(root->left, key);
    else if (key > root->key) root->right = bst_insert(root->right, key);
    // equal key: ignore (this BST holds a set of distinct keys)
    return root;
}

static int bst_contains(const Node *root, int key) {
    while (root) {
        if (key == root->key) return 1;
        root = (key < root->key) ? root->left : root->right;
    }
    return 0;
}

// In-order traversal: left subtree, node, right subtree => keys come out sorted.
static void bst_inorder(const Node *root) {
    if (!root) return;
    bst_inorder(root->left);
    printf("%d ", root->key);
    bst_inorder(root->right);
}

static void bst_free(Node *root) {
    if (!root) return;
    bst_free(root->left);
    bst_free(root->right);
    free(root);
}

// ===== Binary min-heap (array-backed) =======================================
// For node at index i: parent=(i-1)/2, children=2i+1 and 2i+2.
typedef struct {
    int *data;
    size_t size, cap;
} Heap;

static Heap *heap_create(size_t cap) {
    Heap *h = malloc(sizeof(*h));
    if (!h) { perror("malloc"); exit(1); }
    h->data = malloc(cap * sizeof(int));
    if (!h->data) { perror("malloc"); exit(1); }
    h->size = 0; h->cap = cap;
    return h;
}

static void heap_free(Heap *h) { free(h->data); free(h); }

static void swap_int(int *a, int *b) { int t = *a; *a = *b; *b = t; }

// Bubble a new element up until the heap property holds.
static void heap_push(Heap *h, int v) {
    if (h->size == h->cap) {
        h->cap *= 2;
        h->data = realloc(h->data, h->cap * sizeof(int));
        if (!h->data) { perror("realloc"); exit(1); }
    }
    size_t i = h->size++;
    h->data[i] = v;
    while (i > 0) {
        size_t parent = (i - 1) / 2;
        if (h->data[parent] <= h->data[i]) break;
        swap_int(&h->data[parent], &h->data[i]);
        i = parent;
    }
}

// Remove and return the minimum (the root); sift the last element down.
static int heap_pop_min(Heap *h) {
    int top = h->data[0];
    h->data[0] = h->data[--h->size];
    size_t i = 0;
    for (;;) {
        size_t l = 2 * i + 1, r = 2 * i + 2, smallest = i;
        if (l < h->size && h->data[l] < h->data[smallest]) smallest = l;
        if (r < h->size && h->data[r] < h->data[smallest]) smallest = r;
        if (smallest == i) break;
        swap_int(&h->data[i], &h->data[smallest]);
        i = smallest;
    }
    return top;
}

int main(void) {
    // ---- BST demo ----
    printf("=== Binary search tree ===\n");
    int keys[] = {50, 30, 70, 20, 40, 60, 80, 35, 65};
    size_t nk = sizeof keys / sizeof *keys;
    Node *root = NULL;
    printf("insert order: ");
    for (size_t i = 0; i < nk; i++) { printf("%d ", keys[i]); root = bst_insert(root, keys[i]); }
    printf("\nin-order walk (always sorted): ");
    bst_inorder(root);
    printf("\ncontains(40)? %s   contains(99)? %s\n",
           bst_contains(root, 40) ? "yes" : "no",
           bst_contains(root, 99) ? "yes" : "no");
    bst_free(root);

    // ---- Heap / priority queue demo ----
    printf("\n=== Binary min-heap (priority queue) ===\n");
    int items[] = {5, 1, 8, 3, 9, 2, 7, 4, 6};
    size_t ni = sizeof items / sizeof *items;
    Heap *h = heap_create(4);     // small cap on purpose, to exercise growth
    printf("push: ");
    for (size_t i = 0; i < ni; i++) { printf("%d ", items[i]); heap_push(h, items[i]); }
    printf("\npop-min repeatedly (comes out sorted ascending): ");
    while (h->size) printf("%d ", heap_pop_min(h));
    printf("\n");
    heap_free(h);
    return 0;
}
