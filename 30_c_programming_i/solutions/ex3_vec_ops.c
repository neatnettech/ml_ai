// SOLUTION 30.3 — Extend the dynamic array: vec_pop and vec_sum

#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int   *data;
    size_t len;
    size_t cap;
} Vec;

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

int vec_pop(Vec *v) {
    if (v->len == 0) {
        fprintf(stderr, "vec_pop: empty vector\n");
        exit(EXIT_FAILURE);
    }
    v->len--;               // shrink the logical length
    return v->data[v->len]; // the element that was last
}

long vec_sum(const Vec *v) {
    long sum = 0;
    for (size_t i = 0; i < v->len; i++) {
        sum += v->data[i];
    }
    return sum;
}

int main(void) {
    Vec v = vec_new();
    for (int i = 1; i <= 5; i++) vec_push(&v, i);
    printf("sum of [1..5] = %ld\n", vec_sum(&v));
    printf("pop -> %d\n", vec_pop(&v));
    printf("pop -> %d\n", vec_pop(&v));
    printf("len after two pops = %zu\n", v.len);
    printf("sum now = %ld\n", vec_sum(&v));
    vec_free(&v);
    return 0;
}
