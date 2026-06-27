// Module 34 — shared math library: DECLARATIONS
//
// A header is a set of promises: "functions with these names and signatures
// exist somewhere." Callers #include this so the compiler knows the types; the
// LINKER later connects each call to the definition in mymath.c (or in the
// archive libmymath.a / shared object libmymath.dylib built from it).

#ifndef MYMATH_H
#define MYMATH_H

// Greatest common divisor (Euclid). External linkage: defined in mymath.c.
int mm_gcd(int a, int b);

// Integer power base^exp for exp >= 0. External linkage.
long mm_ipow(int base, int exp);

#endif  // MYMATH_H
