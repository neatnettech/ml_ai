// Module 34 — shared math library: DEFINITIONS
//
// This is one translation unit. Compiled with `clang -c` it becomes mymath.o:
// machine code plus a symbol table that EXPORTS mm_gcd and mm_ipow. Both the
// static archive (libmymath.a) and the dynamic library (libmymath.dylib) are
// built from this same source.

#include "mymath.h"

int mm_gcd(int a, int b) {
    if (a < 0) a = -a;
    if (b < 0) b = -b;
    while (b != 0) {
        int t = a % b;
        a = b;
        b = t;
    }
    return a;
}

long mm_ipow(int base, int exp) {
    long result = 1;
    for (int i = 0; i < exp; i++) {
        result *= base;
    }
    return result;
}
