// Exercise 31.1 — Extend the multi-file library: add lcm()
//
// THE MULTI-FILE EDIT LOOP. To add a function to mathlib you touch THREE places:
//   1. declare it in ../mathlib.h   (the promise)
//   2. define  it in ../mathlib.c   (the code)        <- shared with the solution build
//   3. call    it here              (the use)
// The Makefile recompiles only the changed translation units, then relinks.
//
// Your task:
//   (a) Open ../mathlib.h and add:   int lcm(int a, int b);
//   (b) Open ../mathlib.c and define lcm using the EXISTING gcd:
//          lcm(a,b) = |a / gcd(a,b) * b|   (divide first to avoid overflow)
//          define lcm(0,0) and lcm(x,0) to return 0.
//   (c) Build & run:  make ex1     (links ../mathlib.c with this file)
//
// Reference solution: ../solutions/ex1_lcm.c  (and it adds lcm to mathlib too).

#include <stdio.h>
#include "../mathlib.h"

int main(void) {
    // TODO: once you have declared+defined lcm(), uncomment these calls.
    // printf("lcm(4, 6)   = %d  (expected 12)\n", lcm(4, 6));
    // printf("lcm(21, 6)  = %d  (expected 42)\n", lcm(21, 6));
    // printf("lcm(5, 0)   = %d  (expected 0)\n",  lcm(5, 0));

    printf("ex1: declare lcm in mathlib.h, define it in mathlib.c, call it here.\n");
    printf("     then remove this message. See ../solutions/ex1_lcm.c.\n");
    return 0;
}
