// Exercise 30.3 — Extend the dynamic array: vec_pop and vec_sum
//
// Building on 05_dynamic_array.c, add two operations:
//   - vec_pop: remove and return the LAST element (shrinking len, not the buffer).
//   - vec_sum: add up all elements.
// Then `make ex3` should match the expected output in README.md §6.
// Solution in ../solutions/ex3_vec_ops.c.

#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int   *data;
    size_t len;
    size_t cap;
} Vec;

// --- provided: same vector as the demo (new / push / free) -------------------
static Vec vec_new(void) { Vec v = {NULL, 0, 0}; return v; }

static void vec_push(Vec *v, int value) {
    if (v->len == v->cap) {
        size_t new_cap = (v->cap == 0) ? 4 : v->cap * 2;
        int *grown = realloc(v->data, new_cap * sizeof *grown);
        if (grown == NULL) { perror("realloc"); exit(EXIT_FAILURE); }
        v->data = grown;
        v->cap  = new_cap;
    }
    v->data[v->len++] = value;
}

static void vec_free(Vec *v) { free(v->data); v->data = NULL; v->len = v->cap = 0; }
// -----------------------------------------------------------------------------

// Remove and return the last element. Precondition: the vector is non-empty —
// popping an empty vector is a programming error (abort loudly).
int vec_pop(Vec *v) {
    // TODO: if v->len == 0, print an error and exit. Otherwise decrement len and
    // return the element that was at the new len (the old last element).
    (void)v;
    return 0;  // replace this
}

// Return the sum of all elements (0 for an empty vector).
long vec_sum(const Vec *v) {
    // TODO: loop over v->data[0 .. v->len-1] adding into a long accumulator.
    (void)v;
    return 0;  // replace this
}

int main(void) {
    Vec v = vec_new();
    for (int i = 1; i <= 5; i++) vec_push(&v, i);  // 1 2 3 4 5
    printf("sum of [1..5] = %ld\n", vec_sum(&v));
    printf("pop -> %d\n", vec_pop(&v));            // 5
    printf("pop -> %d\n", vec_pop(&v));            // 4
    printf("len after two pops = %zu\n", v.len);   // 3
    printf("sum now = %ld\n", vec_sum(&v));        // 1+2+3 = 6
    vec_free(&v);
    return 0;
}
