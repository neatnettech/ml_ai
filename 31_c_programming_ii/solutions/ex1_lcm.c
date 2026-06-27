// SOLUTION 31.1 — lcm() added across the multi-file library
//
// The header (../mathlib.h) now declares:   int lcm(int a, int b);
// The implementation (../mathlib.c) now defines it in terms of the existing gcd:
//
//     int lcm(int a, int b) {
//         if (a == 0 || b == 0) return 0;
//         int g = gcd(a, b);
//         int r = (a / g) * b;          // divide first to limit overflow
//         return r < 0 ? -r : r;
//     }
//
// This file just CALLS it. `make sol1` compiles ../mathlib.c + this file and links.

#include <stdio.h>
#include "../mathlib.h"

int main(void) {
    printf("lcm(4, 6)   = %d  (expected 12)\n", lcm(4, 6));
    printf("lcm(21, 6)  = %d  (expected 42)\n", lcm(21, 6));
    printf("lcm(5, 0)   = %d  (expected 0)\n",  lcm(5, 0));
    printf("lcm(12, 18) = %d  (expected 36)\n", lcm(12, 18));
    return 0;
}
