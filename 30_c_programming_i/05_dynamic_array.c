// Module 30 — Demo 5: a dynamic array (vector) of ints — the capstone
//
// This pulls together everything: pointers, the heap, malloc/realloc/free, and a
// struct that owns its memory. A "vector" is an array that GROWS: when it fills up,
// we ask realloc for a bigger block (typically 2x), copy the elements over (realloc
// does that for us), and keep going. amortized O(1) push. Build & run: make run5
//
// Read top to bottom alongside README.md §5.

#include <stdio.h>
#include <stdlib.h>

// A vector owns a heap buffer `data`, knows how many ints are in use (`len`), and
// how many it can hold before it must grow (`cap`).
typedef struct {
    int   *data;  // heap-allocated buffer of `cap` ints
    size_t len;   // number of elements currently stored
    size_t cap;   // capacity: how many fit before we must realloc
} Vec;

// Create an empty vector. We start with cap 0 / data NULL and grow lazily, so the
// "empty" case allocates nothing. Returns the vector by value (it's tiny).
static Vec vec_new(void) {
    Vec v = {NULL, 0, 0};
    return v;
}

// Append one element, growing the buffer if it's full.
static void vec_push(Vec *v, int value) {
    if (v->len == v->cap) {                       // full (or empty): grow
        size_t new_cap = (v->cap == 0) ? 4 : v->cap * 2;  // 0 -> 4, else double
        // realloc(NULL, n) acts like malloc(n); realloc of an existing block keeps
        // the old contents and returns a (possibly new) pointer. NEVER assign the
        // result straight back to v->data — if it fails you'd leak the old block.
        int *grown = realloc(v->data, new_cap * sizeof *grown);
        if (grown == NULL) {
            perror("realloc");
            exit(EXIT_FAILURE);
        }
        v->data = grown;
        v->cap  = new_cap;
        printf("    (grew capacity to %zu)\n", v->cap);
    }
    v->data[v->len] = value;  // store, then bump the length
    v->len++;
}

// Read element i. Bounds-checked: out-of-range is a programming error, so we abort
// loudly rather than read garbage (returning a sentinel would hide the bug).
static int vec_get(const Vec *v, size_t i) {
    if (i >= v->len) {
        fprintf(stderr, "vec_get: index %zu out of bounds (len %zu)\n", i, v->len);
        exit(EXIT_FAILURE);
    }
    return v->data[i];
}

// Release the heap buffer and reset the struct so it can't be misused afterward.
static void vec_free(Vec *v) {
    free(v->data);   // free(NULL) is well-defined (a no-op), so empty vecs are fine
    v->data = NULL;
    v->len = v->cap = 0;
}

int main(void) {
    printf("=== Build a vector by pushing; watch it grow ===\n");
    Vec v = vec_new();
    printf("  empty vector: len=%zu cap=%zu data=%p\n",
           v.len, v.cap, (void *)v.data);

    for (int i = 1; i <= 10; i++) {
        printf("  push(%d):\n", i * i);
        vec_push(&v, i * i);  // store the first ten squares
    }

    printf("\n=== Read it back ===\n");
    printf("  len=%zu cap=%zu  (cap >= len; the slack is room to grow)\n",
           v.len, v.cap);
    printf("  contents: ");
    for (size_t i = 0; i < v.len; i++) {
        printf("%d ", vec_get(&v, i));
    }
    putchar('\n');

    vec_free(&v);  // one free balances all the realloc/malloc growth — no leak
    printf("\n  freed. data=%p, len=%zu (safe to reuse or discard)\n",
           (void *)v.data, v.len);

    return 0;
}
