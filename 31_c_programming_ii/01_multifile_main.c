// Module 31 — Demo 1: a MULTI-FILE program (headers, translation units, linking)
//
// This file is one translation unit; mathlib.c is another. Neither knows the
// other's source — they meet only through the header mathlib.h and the linker.
//
//   clang -c mathlib.c            -> mathlib.o          (defines gcd/ipow/is_prime)
//   clang -c 01_multifile_main.c  -> 01_multifile_main.o (CALLS them; unresolved)
//   clang mathlib.o 01_multifile_main.o -o bin/01_multifile   (linker joins them)
//
// Build & run with: make run1   (the Makefile does the two -c steps then links).
// Read alongside README.md §1.

#include <stdio.h>
#include "mathlib.h"   // declarations only — the DEFINITIONS arrive at link time

int main(void) {
    printf("=== gcd ===\n");
    printf("  gcd(48, 36)  = %d\n", gcd(48, 36));
    printf("  gcd(17, 5)   = %d\n", gcd(17, 5));   // coprime -> 1
    printf("  gcd(-12, 8)  = %d\n", gcd(-12, 8));  // handles negatives

    printf("\n=== ipow ===\n");
    printf("  ipow(2, 10)  = %ld\n", ipow(2, 10));
    printf("  ipow(3, 4)   = %ld\n", ipow(3, 4));
    printf("  ipow(5, 0)   = %ld\n", ipow(5, 0));

    printf("\n=== is_prime ===\n");
    printf("  primes < 30: ");
    for (int n = 2; n < 30; n++) {
        if (is_prime(n)) printf("%d ", n);
    }
    putchar('\n');

    return 0;
}
