// Module 30 — Demo 2: Stack vs heap, lifetimes, and the dangling-pointer bug
//
// C has two storage regions you manage by hand:
//   - the STACK: automatic locals, freed automatically when a function returns.
//   - the HEAP:  malloc'd memory that lives until YOU free it.
// The #1 beginner bug is returning a pointer to a stack local — it dangles the
// instant the function returns. We SHOW why without ever dereferencing it
// dangerously. Build & run with: make run2
//
// Read top to bottom alongside README.md §2.

#include <stdio.h>
#include <stdlib.h>

// Show the stack growing DOWNWARD: each nested call's frame sits at a lower
// address than its caller's on typical machines (arm64, x86-64).
static void level3(void) {
    int local = 3;
    printf("    level3: a local lives at %p\n", (void *)&local);
}
static void level2(void) {
    int local = 2;
    printf("   level2: a local lives at %p\n", (void *)&local);
    level3();
}
static void level1(void) {
    int local = 1;
    printf("  level1: a local lives at %p\n", (void *)&local);
    level2();
}

// THE BUG, demonstrated SAFELY. The classic mistake looks like this:
//
//     int *broken_make_int(void) {
//         int n = 99;
//         return &n;     // BUG: &n is dead the instant we return
//     }
//
// We don't write that literally — clang would (rightly) reject it with
// -Werror-style warnings, and dereferencing the result is Undefined Behavior.
// Instead this function just REPORTS the address of its local so you can SEE that
// the slot is reused: call it twice and the same stack address comes back, proving
// the storage is transient and any pointer to it would dangle after return.
static void show_stack_local_address(int tag) {
    int n = tag;
    printf("  call %d: local n=%d lives at %p (this slot is reused after return)\n",
           tag, n, (void *)&n);
}

// THE FIX: allocate on the heap. malloc memory outlives the function; the caller
// owns it and must free() it exactly once.
static int *correct_make_int(void) {
    int *p = malloc(sizeof *p);   // sizeof *p == sizeof(int); idiom that can't go stale
    if (p == NULL) {              // malloc can fail — always check
        perror("malloc");
        exit(EXIT_FAILURE);
    }
    *p = 99;
    printf("  correct_make_int: heap int=%d lives at %p (caller will free it)\n",
           *p, (void *)p);
    return p;  // fine: heap memory lives until free()
}

int main(void) {
    printf("=== Stack frames stack downward (addresses decrease) ===\n");
    int top = 0;
    printf("  main:   a local lives at %p\n", (void *)&top);
    level1();
    printf("  (each deeper call's local sits at a LOWER address — the stack grows down)\n");

    printf("\n=== The dangling-pointer bug (shown safely) ===\n");
    show_stack_local_address(1);
    show_stack_local_address(2);
    printf("  ^ same address twice => that storage is transient. Returning &n from\n");
    printf("    such a function gives the caller a DANGLING pointer; dereferencing it\n");
    printf("    is Undefined Behavior. The fix is the heap, below.\n");

    printf("\n=== The heap fix: malloc / free ===\n");
    int *heap = correct_make_int();
    printf("  *heap = %d  (safe: real, owned memory)\n", *heap);
    free(heap);  // every malloc gets exactly one free — no leaks
    printf("  freed it. (Set heap = NULL after free to avoid use-after-free.)\n");

    printf("\n=== A heap array vs a stack array ===\n");
    int stack_arr[4] = {0};
    printf("  stack array at %p (auto-freed at return)\n", (void *)stack_arr);
    int *heap_arr = malloc(4 * sizeof *heap_arr);  // room for 4 ints
    if (heap_arr == NULL) { perror("malloc"); exit(EXIT_FAILURE); }
    for (int i = 0; i < 4; i++) heap_arr[i] = i * i;
    printf("  heap array  at %p, contents: %d %d %d %d\n",
           (void *)heap_arr, heap_arr[0], heap_arr[1], heap_arr[2], heap_arr[3]);
    free(heap_arr);  // balance the malloc

    return 0;
}
