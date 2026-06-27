// SOLUTION 35.2 — Implement my_calloc and my_realloc

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>

#define HEAP_SIZE 2048

typedef struct block_header { size_t size; int free; } block_header;

static unsigned char heap[HEAP_SIZE];
static int initialized = 0;
#define HDR_SIZE (sizeof(block_header))

static size_t align8(size_t n) { return (n + 7u) & ~(size_t)7u; }

static block_header *next_block(block_header *b) {
    unsigned char *p = (unsigned char *)b + HDR_SIZE + b->size;
    if (p >= heap + HEAP_SIZE) return NULL;
    return (block_header *)p;
}

static void heap_init(void) {
    block_header *first = (block_header *)heap;
    first->size = HEAP_SIZE - HDR_SIZE;
    first->free = 1;
    initialized = 1;
}

void *my_malloc(size_t want) {
    if (!initialized) heap_init();
    if (want == 0) return NULL;
    want = align8(want);
    for (block_header *b = (block_header *)heap; b != NULL; b = next_block(b)) {
        if (!b->free || b->size < want) continue;
        if (b->size >= want + HDR_SIZE + 8) {
            block_header *rest = (block_header *)((unsigned char *)b + HDR_SIZE + want);
            rest->size = b->size - want - HDR_SIZE;
            rest->free = 1;
            b->size = want;
        }
        b->free = 0;
        return (unsigned char *)b + HDR_SIZE;
    }
    return NULL;
}

void my_free(void *ptr) {
    if (!ptr) return;
    block_header *b = (block_header *)((unsigned char *)ptr - HDR_SIZE);
    b->free = 1;
    block_header *n = next_block(b);
    while (n != NULL && n->free) { b->size += HDR_SIZE + n->size; n = next_block(b); }
}

size_t block_payload_size(void *ptr) {
    block_header *b = (block_header *)((unsigned char *)ptr - HDR_SIZE);
    return b->size;
}

void *my_calloc(size_t count, size_t size) {
    if (count != 0 && size > (size_t)-1 / count) return NULL;   // overflow guard
    size_t total = count * size;
    void *p = my_malloc(total);
    if (p) memset(p, 0, total);
    return p;
}

void *my_realloc(void *ptr, size_t size) {
    if (ptr == NULL) return my_malloc(size);
    if (size == 0) { my_free(ptr); return NULL; }
    void *fresh = my_malloc(size);
    if (!fresh) return NULL;
    size_t old = block_payload_size(ptr);
    size_t copy = old < size ? old : size;
    memcpy(fresh, ptr, copy);
    my_free(ptr);
    return fresh;
}

int main(void) {
    heap_init();

    int *z = my_calloc(8, sizeof(int));
    assert(z != NULL);
    for (int i = 0; i < 8; i++) assert(z[i] == 0);
    printf("  my_calloc(8, 4): 32 zeroed bytes at %p\n", (void *)z);

    char *s = my_malloc(8);
    strcpy(s, "1234567");
    char *bigger = my_realloc(s, 64);
    assert(bigger != NULL);
    assert(strcmp(bigger, "1234567") == 0);
    printf("  my_realloc grew the block and kept \"%s\"\n", bigger);

    assert(my_realloc(bigger, 0) == NULL);
    assert(my_calloc((size_t)-1, 2) == NULL);
    my_free(z);

    printf("  OK — all assertions passed.\n");
    return 0;
}
