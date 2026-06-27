// Module 35 — Demo 3: Heap fragmentation
//
// The heap is finite address space carved into blocks. When you free blocks in an
// interleaved pattern, the freed space is split into many small NON-contiguous
// holes. The TOTAL free space may be large, yet no single hole is big enough for a
// large request -- that's *external fragmentation*.
//
// We can't read the system allocator's internal book-keeping portably, so we stay
// honest: we demonstrate the pattern with our OWN slots, then probe the real
// allocator only with claims it can actually support (a request can fail/succeed).
//
// Build & run with: make run3.
//
// Read top to bottom alongside README.md §3.

#include <stdio.h>
#include <stdlib.h>

#define N 16
#define BLOCK 4096   // one page-ish per block, to make the pattern tangible

int main(void) {
    printf("=== Set up: %d blocks of %d bytes ===\n", N, BLOCK);
    void *slots[N];
    for (int i = 0; i < N; i++) {
        slots[i] = malloc(BLOCK);
        if (!slots[i]) { perror("malloc"); return 1; }
    }
    printf("  allocated %d blocks = %d bytes total\n", N, N * BLOCK);

    // Free every OTHER block. Now half the bytes are free, but they sit in
    // alternating holes separated by still-live blocks.
    printf("\n=== Free every other block (interleaved frees) ===\n");
    int freed = 0;
    for (int i = 0; i < N; i += 2) {
        free(slots[i]);
        slots[i] = NULL;
        freed++;
    }
    printf("  freed %d blocks = %d bytes, but in %d separate holes of %d bytes each\n",
           freed, freed * BLOCK, freed, BLOCK);
    printf("  layout (X=live . =hole): ");
    for (int i = 0; i < N; i++) putchar(slots[i] ? 'X' : '.');
    putchar('\n');

    // The honest probe: total free >= one big block, but the holes are scattered.
    // Asking for a block bigger than any single hole MUST come from elsewhere.
    size_t total_free = (size_t)freed * BLOCK;
    size_t big = total_free;   // as big as ALL the holes combined
    printf("\n=== The fragmentation problem ===\n");
    printf("  total freed bytes = %zu, but the biggest single hole = %d\n",
           total_free, BLOCK);
    printf("  a request for %zu contiguous bytes cannot reuse those holes --\n", big);
    void *one_big = malloc(big);
    printf("  malloc(%zu) %s (it had to grow the heap / use a fresh region)\n",
           big, one_big ? "succeeded" : "FAILED");
    free(one_big);

    // Meanwhile a request that FITS a hole can be served from the freed space.
    void *fits = malloc(BLOCK);
    printf("  malloc(%d) (fits one hole) %s\n", BLOCK, fits ? "succeeded" : "FAILED");
    free(fits);

    printf("\n=== Takeaway ===\n");
    printf("  Free space is necessary but not sufficient: it must be CONTIGUOUS.\n");
    printf("  Real allocators fight this with size classes, coalescing, and arenas\n");
    printf("  -- you'll build a tiny coalescing allocator in demo 4.\n");

    for (int i = 1; i < N; i += 2) free(slots[i]);   // clean up the survivors
    return 0;
}
