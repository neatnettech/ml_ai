// Module 31 — mathlib.c : the IMPLEMENTATION (definitions) for mathlib.h.
//
// This is a separate TRANSLATION UNIT. The compiler turns it into an object file
// (mathlib.o) full of machine code with the symbols `gcd`, `ipow`, `is_prime`.
// It is compiled WITHOUT any main() — it is a library of parts. The linker later
// resolves the calls in 01_multifile_main.o against the symbols defined here.
//
// We include our own header so the compiler can check that the definitions below
// MATCH the declarations (same signatures) — a cheap, valuable consistency check.

#include "mathlib.h"

int gcd(int a, int b) {
    // Work on magnitudes so negative inputs behave sensibly.
    if (a < 0) a = -a;
    if (b < 0) b = -b;
    // Euclid: gcd(a, b) == gcd(b, a mod b), terminating when b hits 0.
    while (b != 0) {
        int t = a % b;
        a = b;
        b = t;
    }
    return a;
}

long ipow(int base, int exp) {
    if (exp < 0) return 0;          // not meaningful in integers; caller's problem
    long result = 1;
    for (int i = 0; i < exp; i++) {
        result *= base;             // may overflow for big inputs — that's on you
    }
    return result;
}

int is_prime(int n) {
    if (n < 2) return 0;            // 0, 1, and negatives are not prime
    if (n % 2 == 0) return n == 2;  // 2 is prime; all other evens are not
    // Only test odd divisors up to sqrt(n): if d*d > n and nothing divided n, it's
    // prime. We compare d*d <= n instead of computing a square root.
    for (int d = 3; d <= n / d; d += 2) {
        if (n % d == 0) return 0;
    }
    return 1;
}

int lcm(int a, int b) {
    if (a == 0 || b == 0) return 0;
    int g = gcd(a, b);
    // Divide BEFORE multiplying so the intermediate value stays small (avoids
    // overflowing a*b for moderately large inputs). Take the magnitude of the
    // result so a negative input doesn't produce a negative "multiple".
    int r = (a / g) * b;
    return r < 0 ? -r : r;
}
