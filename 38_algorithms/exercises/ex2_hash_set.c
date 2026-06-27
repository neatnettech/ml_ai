// Exercise 38.2 — A hash SET of strings
//
// A set is a hash table that stores keys only (no values). Implement `set_add`
// (insert if absent) and `set_contains` (membership test) using separate chaining,
// the same idea as demo 3. Then `make ex2` should match `make sol2`.
// Solution in ../solutions/ex2_hash_set.c.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned long hash_str(const char *s) {
    unsigned long h = 5381;
    int c;
    while ((c = (unsigned char)*s++)) h = ((h << 5) + h) + (unsigned long)c;
    return h;
}

typedef struct SNode {
    char *key;
    struct SNode *next;
} SNode;

typedef struct {
    SNode **buckets;
    size_t nbuckets;
    size_t size;
} StrSet;

static StrSet *set_create(size_t nbuckets) {
    StrSet *s = malloc(sizeof(*s));
    if (!s) { perror("malloc"); exit(1); }
    s->buckets = calloc(nbuckets, sizeof(SNode *));
    if (!s->buckets) { perror("calloc"); exit(1); }
    s->nbuckets = nbuckets;
    s->size = 0;
    return s;
}

// Return 1 if `key` is in the set, else 0.
static int set_contains(const StrSet *s, const char *key) {
    // TODO: hash key to a bucket, walk the chain, strcmp each entry; return 1 on hit.
    (void)s; (void)key; (void)hash_str;   // remove these once you use them
    return 0;
}

// Add `key` if not already present. Return 1 if newly added, 0 if it was a dup.
static int set_add(StrSet *s, const char *key) {
    // TODO:
    //  1. if set_contains(s, key) -> return 0 (no duplicate stored)
    //  2. otherwise allocate an SNode, strdup the key, push it to the front of
    //     the bucket chain, bump s->size, return 1
    (void)s; (void)key;
    return 0;
}

static void set_free(StrSet *s) {
    for (size_t i = 0; i < s->nbuckets; i++) {
        SNode *e = s->buckets[i];
        while (e) { SNode *n = e->next; free(e->key); free(e); e = n; }
    }
    free(s->buckets);
    free(s);
}

int main(void) {
    StrSet *s = set_create(8);
    const char *words[] = {"red", "green", "blue", "red", "green", "yellow"};
    size_t n = sizeof words / sizeof *words;

    printf("adding: ");
    for (size_t i = 0; i < n; i++)
        printf("%s(%s) ", words[i], set_add(s, words[i]) ? "new" : "dup");
    printf("\nsize = %zu  (expected 4: red green blue yellow)\n", s->size);

    const char *probes[] = {"blue", "purple", "red"};
    for (size_t i = 0; i < sizeof probes / sizeof *probes; i++)
        printf("contains(\"%s\") = %d\n", probes[i], set_contains(s, probes[i]));

    set_free(s);
    return 0;
}
