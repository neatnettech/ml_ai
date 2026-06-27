// SOLUTION 38.2 — A hash SET of strings (separate chaining)

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

static int set_contains(const StrSet *s, const char *key) {
    size_t idx = hash_str(key) % s->nbuckets;
    for (SNode *e = s->buckets[idx]; e; e = e->next)
        if (strcmp(e->key, key) == 0) return 1;
    return 0;
}

static int set_add(StrSet *s, const char *key) {
    if (set_contains(s, key)) return 0;
    size_t idx = hash_str(key) % s->nbuckets;
    SNode *e = malloc(sizeof(*e));
    if (!e) { perror("malloc"); exit(1); }
    e->key = strdup(key);
    if (!e->key) { perror("strdup"); exit(1); }
    e->next = s->buckets[idx];
    s->buckets[idx] = e;
    s->size++;
    return 1;
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
