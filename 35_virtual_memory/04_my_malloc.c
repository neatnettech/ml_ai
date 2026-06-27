// Module 35 — Demo 4: my_malloc — a tiny allocator over a static byte buffer
//
// This is the Malloc-Lab idea, simplified and native: we manage one fixed byte
// array ourselves. Each block starts with a HEADER (size of its payload + a free
// flag); blocks sit back-to-back, so "next block" is just header + size away. We
// use a FIRST-FIT search and COALESCE adjacent free blocks on free() to fight the
// fragmentation you saw in demo 3.
//
// Build & run with: make run4.
//
// Read top to bottom alongside README.md §4.

#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define HEAP_SIZE 1024   // our entire "RAM", in bytes

// 8-byte aligned header so payloads are aligned too. `size` is the PAYLOAD size in
// bytes; `free` is 1 if the block is available.
typedef struct block_header {
    size_t size;
    int    free;
} block_header;

static unsigned char heap[HEAP_SIZE];
static int initialized = 0;

#define HDR_SIZE (sizeof(block_header))

// Round up to a multiple of 8 so every payload starts aligned.
static size_t align8(size_t n) { return (n + 7u) & ~(size_t)7u; }

// The block immediately after `b` in the buffer, or NULL if `b` is the last one.
static block_header *next_block(block_header *b) {
    unsigned char *p = (unsigned char *)b + HDR_SIZE + b->size;
    if (p >= heap + HEAP_SIZE) return NULL;
    return (block_header *)p;
}

static void heap_init(void) {
    block_header *first = (block_header *)heap;
    first->size = HEAP_SIZE - HDR_SIZE;   // one big free block fills the buffer
    first->free = 1;
    initialized = 1;
}

void *my_malloc(size_t want) {
    if (!initialized) heap_init();
    if (want == 0) return NULL;
    want = align8(want);

    // First fit: walk blocks, take the first free one that's big enough.
    for (block_header *b = (block_header *)heap; b != NULL; b = next_block(b)) {
        if (!b->free || b->size < want) continue;

        // Split if the leftover is big enough to hold a header + a little payload.
        if (b->size >= want + HDR_SIZE + 8) {
            block_header *rest = (block_header *)((unsigned char *)b + HDR_SIZE + want);
            rest->size = b->size - want - HDR_SIZE;
            rest->free = 1;
            b->size = want;
        }
        b->free = 0;
        return (unsigned char *)b + HDR_SIZE;   // hand back the payload, not the header
    }
    return NULL;   // no fit
}

// Coalesce: after marking a block free, merge it with the following block while
// that neighbour is also free. (Repeated free()s thus glue the whole run together.)
void my_free(void *ptr) {
    if (!ptr) return;
    block_header *b = (block_header *)((unsigned char *)ptr - HDR_SIZE);
    b->free = 1;

    block_header *n = next_block(b);
    while (n != NULL && n->free) {
        b->size += HDR_SIZE + n->size;   // absorb header + payload of the neighbour
        n = next_block(b);
    }
}

// Print every block in order: a quick X-ray of the heap's state.
static void dump_heap(const char *label) {
    printf("  %-22s", label);
    int blocks = 0;
    size_t used = 0, freeb = 0;
    for (block_header *b = (block_header *)heap; b != NULL; b = next_block(b)) {
        printf("[%zu %s]", b->size, b->free ? "free" : "USED");
        if (b->free) freeb += b->size; else used += b->size;
        blocks++;
    }
    printf("   (%d blocks, %zu used, %zu free)\n", blocks, used, freeb);
}

int main(void) {
    printf("=== A %d-byte heap, header = %zu bytes ===\n", HEAP_SIZE, HDR_SIZE);
    heap_init();
    dump_heap("empty:");

    printf("\n=== Three allocations ===\n");
    char *a = my_malloc(100);
    char *b = my_malloc(200);
    char *c = my_malloc(50);
    printf("  a=%p b=%p c=%p (distinct, usable regions)\n",
           (void *)a, (void *)b, (void *)c);
    strcpy(a, "block A");          // prove each region is independently writable
    strcpy(b, "block B");
    strcpy(c, "block C");
    printf("  wrote: \"%s\" \"%s\" \"%s\"\n", a, b, c);
    dump_heap("after 3 mallocs:");

    printf("\n=== Free the middle block (leaves a hole) ===\n");
    my_free(b);
    dump_heap("after free(b):");

    printf("\n=== Free its neighbours -> coalescing ===\n");
    my_free(c);   // c is now adjacent to the trailing free block; they merge
    dump_heap("after free(c):");
    my_free(a);   // a is now followed by free(b), free(c), trailing -> all merge
    dump_heap("after free(a):");
    printf("  the holes merged forward into one big free block.\n");

    printf("\n=== Reuse the coalesced space ===\n");
    char *big = my_malloc(300);
    printf("  my_malloc(300) %s at %p\n", big ? "succeeded" : "FAILED", (void *)big);
    dump_heap("after malloc(300):");
    my_free(big);

    return 0;
}
