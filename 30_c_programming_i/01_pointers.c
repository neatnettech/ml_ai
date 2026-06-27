// Module 30 — Demo 1: Pointers, the & and * operators, and pass-by-pointer
//
// A pointer is just a variable whose value is a MEMORY ADDRESS. C exposes the
// machine's memory model directly: every object lives at some address, `&x` gives
// you that address, and `*p` follows an address back to the object it names.
// This is the whole reason C is in this track. Build & run with: make run1
//
// Read top to bottom alongside README.md §1.

#include <stdio.h>

// pass-by-VALUE: `n` is a COPY of the caller's variable. Changing it here has no
// effect on the caller — the copy is discarded when the function returns.
static void add_one_by_value(int n) {
    n = n + 1;  // mutates the local copy only
}

// pass-by-POINTER: we receive the ADDRESS of the caller's variable, so `*p` reads
// and writes the caller's actual object. This is how C does "output parameters".
static void add_one_by_pointer(int *p) {
    *p = *p + 1;  // dereference: follow the address, then write through it
}

// The classic swap: impossible by value (you'd swap copies), trivial by pointer.
static void swap(int *a, int *b) {
    int tmp = *a;  // save the value a points to
    *a = *b;       // write b's value into a's object
    *b = tmp;      // write the saved value into b's object
}

int main(void) {
    printf("=== Variables have addresses ===\n");
    int x = 42;
    int y = 7;
    // %p prints a pointer; the standard wants a void* argument, so we cast.
    printf("  x = %d  lives at address &x = %p\n", x, (void *)&x);
    printf("  y = %d  lives at address &y = %p\n", y, (void *)&y);
    printf("  (these addresses change every run — that's normal)\n");

    printf("\n=== A pointer holds an address; * follows it ===\n");
    int *p = &x;            // p now holds the address of x
    printf("  p   = %p   (the value stored IN p is x's address)\n", (void *)p);
    printf("  *p  = %d    (dereference: the int p points at)\n", *p);
    *p = 100;               // write THROUGH the pointer...
    printf("  after *p = 100, x is now %d  (we changed x via p)\n", x);

    printf("\n=== Pass by value vs pass by pointer ===\n");
    x = 5;
    add_one_by_value(x);
    printf("  add_one_by_value(x): x is still %d (copy was changed, not x)\n", x);
    add_one_by_pointer(&x);
    printf("  add_one_by_pointer(&x): x is now %d (changed through the address)\n", x);

    printf("\n=== swap really swaps ===\n");
    printf("  before: x = %d, y = %d\n", x, y);
    swap(&x, &y);
    printf("  after : x = %d, y = %d\n", x, y);

    printf("\n=== Arrays decay to pointers; pointer arithmetic ===\n");
    int a[5] = {10, 20, 30, 40, 50};
    // In most expressions an array NAME becomes a pointer to its first element.
    // So `a` and `&a[0]` are the same address, and a[i] == *(a + i).
    int *q = a;  // implicit decay: q points at a[0]
    printf("  a       = %p   (array name decays to &a[0])\n", (void *)a);
    printf("  &a[0]   = %p   (same address)\n", (void *)&a[0]);
    printf("  a[2] = %d, *(a + 2) = %d  (identical: indexing IS pointer math)\n",
           a[2], *(a + 2));

    // Pointer arithmetic counts in ELEMENTS, not bytes: q + 1 advances by
    // sizeof(int) bytes, not 1. Walk the array with a moving pointer:
    printf("  walking with a pointer: ");
    for (int *it = a; it < a + 5; it++) {  // it++ steps by one int
        printf("%d ", *it);
    }
    putchar('\n');
    // The byte gap between consecutive elements equals sizeof(int):
    printf("  (q+1) - q = %ld element, = %zu bytes apart in memory\n",
           (long)((q + 1) - q), sizeof(int));

    return 0;
}
