// Exercise 35.2 — Implement my_calloc and my_realloc
//
// A complete coalescing allocator (my_malloc / my_free) is given below, plus a
// helper block_payload_size(ptr) that returns how many usable bytes a live block
// has. Build the two standard cousins on top:
//
//   my_calloc(count, size) — allocate count*size bytes, ZEROED. Guard the multiply
//                            against overflow (return NULL if count*size overflows).
//   my_realloc(ptr, size)  — resize a block. Rules: realloc(NULL, n) == malloc(n);
//                            realloc(p, 0) frees p and returns NULL; otherwise
//                            allocate the new size, copy min(old, new) bytes, free p.
//
// Verify with `make ex2` — the asserts at the bottom must all pass and it prints OK.
// Solution in ../solutions/ex2_calloc_realloc.c; README §6.

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

// Usable payload bytes of a live block — handy for realloc's copy step.
size_t block_payload_size(void *ptr) {
    block_header *b = (block_header *)((unsigned char *)ptr - HDR_SIZE);
    return b->size;
}

void *my_calloc(size_t count, size_t size) {
    // TODO: compute count*size with overflow check, my_malloc it, zero it, return.
    (void)count; (void)size;
    return NULL;
}

void *my_realloc(void *ptr, size_t size) {
    // TODO: handle the NULL and 0 cases, then allocate new, copy
    //       min(block_payload_size(ptr), size) bytes, free old, return new.
    (void)ptr; (void)size;
    return NULL;
}

int main(void) {
    heap_init();

    int *z = my_calloc(8, sizeof(int));
    assert(z != NULL);
    for (int i = 0; i < 8; i++) assert(z[i] == 0);   // calloc zeroes
    printf("  my_calloc(8, 4): 32 zeroed bytes at %p\n", (void *)z);

    char *s = my_malloc(8);
    strcpy(s, "1234567");
    char *bigger = my_realloc(s, 64);                 // grow, keep contents
    assert(bigger != NULL);
    assert(strcmp(bigger, "1234567") == 0);
    printf("  my_realloc grew the block and kept \"%s\"\n", bigger);

    assert(my_realloc(bigger, 0) == NULL);            // realloc(p,0) frees
    assert(my_calloc((size_t)-1, 2) == NULL);         // overflow rejected
    my_free(z);

    printf("  OK — all assertions passed.\n");
    return 0;
}
