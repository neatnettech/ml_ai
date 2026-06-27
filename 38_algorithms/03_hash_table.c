// Module 38 — Demo 3: A hash table (separate chaining)
//
// A hash table maps keys to values in average O(1). We hash a string to a bucket
// index, and store collisions as a linked list in that bucket (separate chaining).
// Insert / lookup / delete are all here, plus a load-factor report so you can see
// why "average O(1)" holds: with a good hash, buckets stay short.
// Build & run with: make run3
//
// Read top to bottom alongside README.md §3.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// djb2 string hash (Dan Bernstein): simple, fast, decent spread for short keys.
static unsigned long hash_str(const char *s) {
    unsigned long h = 5381;
    int c;
    while ((c = (unsigned char)*s++)) h = ((h << 5) + h) + (unsigned long)c; // h*33 + c
    return h;
}

typedef struct Entry {
    char *key;
    int value;
    struct Entry *next;        // next entry in the same bucket (collision chain)
} Entry;

typedef struct {
    Entry **buckets;
    size_t nbuckets;
    size_t size;               // number of stored key/value pairs
} HashTable;

static HashTable *ht_create(size_t nbuckets) {
    HashTable *h = malloc(sizeof(*h));
    if (!h) { perror("malloc"); exit(1); }
    h->buckets = calloc(nbuckets, sizeof(Entry *));
    if (!h->buckets) { perror("calloc"); exit(1); }
    h->nbuckets = nbuckets;
    h->size = 0;
    return h;
}

// Insert or overwrite. Returns the bucket index used (handy for the demo).
static size_t ht_put(HashTable *h, const char *key, int value) {
    size_t idx = hash_str(key) % h->nbuckets;
    for (Entry *e = h->buckets[idx]; e; e = e->next) {
        if (strcmp(e->key, key) == 0) { e->value = value; return idx; }
    }
    Entry *e = malloc(sizeof(*e));
    if (!e) { perror("malloc"); exit(1); }
    e->key = strdup(key);
    if (!e->key) { perror("strdup"); exit(1); }
    e->value = value;
    e->next = h->buckets[idx];    // push to front of the chain
    h->buckets[idx] = e;
    h->size++;
    return idx;
}

// Lookup. Returns 1 and writes *out if found, else 0.
static int ht_get(const HashTable *h, const char *key, int *out) {
    size_t idx = hash_str(key) % h->nbuckets;
    for (Entry *e = h->buckets[idx]; e; e = e->next) {
        if (strcmp(e->key, key) == 0) { if (out) *out = e->value; return 1; }
    }
    return 0;
}

// Delete. Returns 1 if a key was removed, else 0.
static int ht_del(HashTable *h, const char *key) {
    size_t idx = hash_str(key) % h->nbuckets;
    Entry **link = &h->buckets[idx];
    while (*link) {
        Entry *e = *link;
        if (strcmp(e->key, key) == 0) {
            *link = e->next;
            free(e->key);
            free(e);
            h->size--;
            return 1;
        }
        link = &e->next;
    }
    return 0;
}

static void ht_free(HashTable *h) {
    for (size_t i = 0; i < h->nbuckets; i++) {
        Entry *e = h->buckets[i];
        while (e) { Entry *n = e->next; free(e->key); free(e); e = n; }
    }
    free(h->buckets);
    free(h);
}

// Report load factor and the longest collision chain — the "is it O(1)?" check.
static void ht_stats(const HashTable *h) {
    size_t longest = 0, used = 0;
    for (size_t i = 0; i < h->nbuckets; i++) {
        size_t len = 0;
        for (Entry *e = h->buckets[i]; e; e = e->next) len++;
        if (len) used++;
        if (len > longest) longest = len;
    }
    printf("  entries=%zu buckets=%zu load=%.2f  used buckets=%zu  longest chain=%zu\n",
           h->size, h->nbuckets, (double)h->size / (double)h->nbuckets, used, longest);
}

int main(void) {
    printf("=== Hash table (separate chaining), djb2 string hash ===\n\n");

    HashTable *h = ht_create(16);

    const char *fruits[] = {"apple", "banana", "cherry", "date", "elderberry",
                            "fig", "grape", "honeydew", "kiwi", "lemon"};
    size_t nf = sizeof fruits / sizeof *fruits;

    printf("Insert 10 keys; note which bucket each lands in (collisions share one):\n");
    for (size_t i = 0; i < nf; i++) {
        size_t b = ht_put(h, fruits[i], (int)(i + 1));
        printf("  put(\"%-10s\", %2zu) -> bucket %2zu\n", fruits[i], i + 1, b);
    }
    printf("\n");
    ht_stats(h);

    printf("\nLookups (average O(1) — at most one short chain to walk):\n");
    int v;
    const char *probes[] = {"cherry", "lemon", "mango" /* absent */};
    for (size_t i = 0; i < sizeof probes / sizeof *probes; i++) {
        if (ht_get(h, probes[i], &v))
            printf("  get(\"%s\") = %d\n", probes[i], v);
        else
            printf("  get(\"%s\") = (not found)\n", probes[i]);
    }

    printf("\nDelete \"banana\", then look it up again:\n");
    printf("  del(\"banana\") = %d\n", ht_del(h, "banana"));
    printf("  get(\"banana\") = %s\n", ht_get(h, "banana", &v) ? "found" : "(not found)");
    printf("  del(\"banana\") again = %d  (already gone)\n", ht_del(h, "banana"));

    printf("\nFinal state:\n  ");
    ht_stats(h);

    ht_free(h);
    return 0;
}
