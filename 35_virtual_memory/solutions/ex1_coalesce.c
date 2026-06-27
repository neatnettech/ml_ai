// SOLUTION 35.1 — Add coalescing to a free-list allocator

#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define HEAP_SIZE 640   // sized so no single hole fits the final 300-byte request

typedef struct block_header {
    size_t size;
    int    free;
} block_header;

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
    // Coalesce forward: absorb each following free block into this one.
    block_header *n = next_block(b);
    while (n != NULL && n->free) {
        b->size += HDR_SIZE + n->size;
        n = next_block(b);
    }
}

static void dump_heap(const char *label) {
    printf("  %-22s", label);
    int blocks = 0; size_t used = 0, freeb = 0;
    for (block_header *b = (block_header *)heap; b != NULL; b = next_block(b)) {
        printf("[%zu %s]", b->size, b->free ? "free" : "USED");
        if (b->free) freeb += b->size; else used += b->size;
        blocks++;
    }
    printf("   (%d blocks, %zu used, %zu free)\n", blocks, used, freeb);
}

int main(void) {
    heap_init();
    char *a = my_malloc(100);
    char *b = my_malloc(200);
    char *c = my_malloc(50);
    dump_heap("after 3 mallocs:");
    my_free(b); dump_heap("after free(b):");
    my_free(c); dump_heap("after free(c):");
    my_free(a); dump_heap("after free(a):");
    char *big = my_malloc(300);
    printf("  my_malloc(300) %s\n", big ? "succeeded" : "FAILED (needs coalescing!)");
    dump_heap("after malloc(300):");
    my_free(big);
    return 0;
}
