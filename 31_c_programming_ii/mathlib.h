// Module 31 — mathlib.h : the PUBLIC INTERFACE of our little math library.
//
// A header file contains DECLARATIONS — promises about what exists — not the code
// that does the work. Anyone who wants to call gcd(), ipow(), or is_prime() does
// NOT need the source; they just #include this header so the compiler knows the
// function names, parameter types, and return types. The actual CODE lives in
// mathlib.c (the definitions), compiled separately, and joined to the caller by
// the LINKER. That separation is the whole point of demo 1 — see README §1.

// ---- Include guard -------------------------------------------------------------
// If two files both #include "mathlib.h" (directly or transitively), the
// preprocessor would paste these declarations in twice. Re-declaring is usually
// harmless, but re-defining a struct/typedef is an error. The guard makes the body
// expand only the FIRST time the token MATHLIB_H is seen.
#ifndef MATHLIB_H
#define MATHLIB_H

// Greatest common divisor of a and b (Euclid's algorithm). Operates on the
// absolute values; gcd(0, 0) is defined here to return 0.
int gcd(int a, int b);

// Integer power: base raised to a non-negative exponent, computed in pure integer
// arithmetic (no floating point). exp < 0 returns 0 (undefined for our purposes).
long ipow(int base, int exp);

// Primality test. Returns 1 if n is prime, 0 otherwise. n < 2 is not prime.
int is_prime(int n);

// Least common multiple of a and b, built on gcd. lcm(x, 0) and lcm(0, 0) are 0.
// (Added in Exercise 31.1 — this is the "edit the header" step of the multi-file
// loop; the matching definition is in mathlib.c.)
int lcm(int a, int b);

#endif // MATHLIB_H
