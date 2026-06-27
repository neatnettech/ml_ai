// Module 31 — Demo 4: UNDEFINED BEHAVIOR (UB), demonstrated SAFELY
//
// The C standard leaves many situations "undefined": the compiler may do anything
// — return garbage, crash, or (worst) silently "work" today and miscompile
// tomorrow. UB is the bargain that makes C fast: the compiler ASSUMES you never
// trigger it and optimizes accordingly. It is also why C is dangerous, and why the
// debugging tools in demo 5 exist.
//
// This program does NOT actually execute UB (that would make the demo's output
// meaningless and could crash). For each classic UB it (a) explains the trap and
// (b) shows the DEFINED, correct alternative. Build & run with: make run4.
// Read alongside README.md §4.

#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <string.h>

int main(void) {
    printf("=== 1. Signed integer overflow ===\n");
    // INT_MAX + 1 as a signed int is UNDEFINED — not "wraps to INT_MIN". The
    // compiler may assume it never happens (e.g. that x+1 > x is always true).
    // DEFINED alternative: compute in UNSIGNED, where wrap is guaranteed modulo 2^N,
    // then reinterpret if you really want the wrapped bit pattern.
    int max = INT_MAX;
    unsigned wrapped = (unsigned)max + 1u;        // defined: modular arithmetic
    printf("  INT_MAX            = %d\n", max);
    printf("  (signed) INT_MAX+1 = UNDEFINED BEHAVIOR (do not rely on it)\n");
    printf("  unsigned INT_MAX+1 = %u  (defined: wraps mod 2^32)\n", wrapped);
    // Safe overflow CHECK: test before you add, never after.
    int a = 2000000000, b = 2000000000;
    if (a > INT_MAX - b)
        printf("  a + b would overflow -> refused (checked a > INT_MAX - b)\n");

    printf("\n=== 2. Out-of-bounds array access ===\n");
    // Reading/writing past the end of an array is UB — it may read junk, corrupt
    // neighbors, or crash. There is no bounds checking in C. The defense is to
    // carry the length and check the index yourself.
    int arr[5] = {10, 20, 30, 40, 50};
    size_t len = sizeof arr / sizeof arr[0];
    int idx = 7;                                   // intentionally out of range
    if (idx >= 0 && (size_t)idx < len)
        printf("  arr[%d] = %d\n", idx, arr[idx]);
    else
        printf("  arr[%d]: out of bounds (len=%zu) -> refused, not read\n", idx, len);
    printf("  in-bounds arr[4] = %d  (the checked, defined access)\n", arr[4]);

    printf("\n=== 3. Use-after-free / dangling pointer ===\n");
    // After free(p), the pointer still holds an address but the memory is gone.
    // DEREFERENCING it is UB. The discipline: set the pointer to NULL right after
    // freeing, then a stray use crashes loudly (NULL deref) instead of silently
    // reading reclaimed memory.
    char *p = malloc(16);
    if (p) {
        strcpy(p, "live data");
        printf("  before free: p = \"%s\"\n", p);
        free(p);
        p = NULL;                                  // the safety habit
        printf("  after free + p=NULL: dereferencing p would be UB; p is now NULL\n");
    }
    if (p == NULL) printf("  guarded: we check p != NULL before any use\n");

    printf("\n=== 4. Reading an uninitialized variable ===\n");
    // An automatic (stack) variable starts with INDETERMINATE contents; reading it
    // before assignment is UB. Always initialize at declaration.
    int initialized = 0;                           // the fix: give it a value
    printf("  uninitialized int: reading it is UB (could be any bit pattern)\n");
    printf("  initialized int = %d  (always assign before you read)\n", initialized);

    printf("\nTakeaway: UB is the compiler's license to optimize hard — it ASSUMES\n");
    printf("you never do these. Tools (demo 5) catch the cases discipline misses.\n");
    return 0;
}
