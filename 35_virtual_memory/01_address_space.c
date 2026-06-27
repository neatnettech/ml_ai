// Module 35 — Demo 1: The process address space
//
// Every process sees its own private, contiguous virtual address space. The kernel
// (with the MMU) translates those virtual addresses to physical RAM behind the
// scenes. This program prints the address of one symbol from each classic region —
// text (code), data, bss, heap, stack — so you can SEE the layout and ordering.
//
// Build & run with: make run1   (addresses VARY between runs because of ASLR.)
//
// Read top to bottom alongside README.md §1.

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

// A global with an initializer lives in the DATA segment.
int g_initialized = 42;
// A global left uninitialized (or zero) lives in BSS (zeroed at load time).
int g_uninitialized;

// A function lives in the TEXT (code) segment.
static void a_function(void) { /* nothing; we only want its address */ }

int main(void) {
    int local = 7;                       // on the STACK
    int *heap = malloc(sizeof *heap);    // points into the HEAP
    if (!heap) { perror("malloc"); return 1; }
    *heap = 99;

    // %p prints a pointer; cast to void* as the standard requires. uintptr-style
    // ordering is what we care about, not the absolute numbers.
    printf("=== One process, five regions (low address -> high) ===\n");
    printf("  text   (code)        %p   a_function\n",   (void *)a_function);
    printf("  data   (init global) %p   g_initialized=%d\n",
           (void *)&g_initialized, g_initialized);
    printf("  bss    (zero global) %p   g_uninitialized=%d\n",
           (void *)&g_uninitialized, g_uninitialized);
    printf("  heap   (malloc)      %p   *heap=%d\n", (void *)heap, *heap);
    printf("  stack  (local)       %p   local=%d\n", (void *)&local, local);

    printf("\n=== Typical ordering ===\n");
    printf("  text < data <= bss < heap   ...grows up...\n");
    printf("  stack is way up high         ...grows down...\n");
    printf("  heap %p  <  stack %p ? %s\n", (void *)heap, (void *)&local,
           (void *)heap < (void *)&local ? "yes (heap below stack)" : "no");

    printf("\n=== ASLR ===\n");
    printf("  Run this again: the addresses change. The kernel randomizes the base\n");
    printf("  of each region every exec so an attacker can't predict them.\n");

    printf("\n=== Page size ===\n");
    printf("  getpagesize() = %d bytes\n", getpagesize());
    printf("  Virtual memory is handed out one PAGE at a time, not one byte.\n");

    free(heap);
    return 0;
}
