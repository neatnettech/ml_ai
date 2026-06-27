// Module 29 — Demo 1: One primitive gate (NAND) builds every logic gate
//
// The whole of digital logic can be built from a SINGLE gate: NAND ("not-and").
// This is the central idea behind Nand2Tetris. Here we define nand() as our ONLY
// primitive, then construct NOT, AND, OR, and XOR using nothing but nand(), and
// print the truth table of each so you can verify it by eye. Build & run: make run1
//
// Read top to bottom alongside README.md §1.
//
// Convention: a "bit" is a C int that is 0 or 1. We never use other values.

#include <stdio.h>

// ---- THE ONE PRIMITIVE -------------------------------------------------------
// NAND(a,b) = NOT(a AND b). Output is 0 only when BOTH inputs are 1.
// This is the only gate we are "allowed" to assume exists; everything else is
// derived from it. (In real silicon a NAND is ~4 transistors — cheap and complete.)
static int nand(int a, int b) {
    return !(a && b);
}

// ---- EVERYTHING ELSE, BUILT FROM NAND ONLY -----------------------------------

// NOT a = NAND(a,a). Feeding the same wire into both inputs: when a=1 -> NAND=0,
// when a=0 -> NAND=1. So a single NAND with tied inputs is an inverter.
static int gate_not(int a) {
    return nand(a, a);
}

// AND a,b = NOT(NAND(a,b)). NAND already gives us NOT-AND, so invert it again.
static int gate_and(int a, int b) {
    return gate_not(nand(a, b));
}

// OR a,b = NAND(NOT a, NOT b). By De Morgan's law: a OR b == NOT(NOT a AND NOT b),
// and NAND(x,y) == NOT(x AND y), so NAND(NOT a, NOT b) == NOT(NOT a AND NOT b).
static int gate_or(int a, int b) {
    return nand(gate_not(a), gate_not(b));
}

// XOR a,b = 1 when the inputs DIFFER. A classic 4-NAND construction:
//   c = NAND(a,b)
//   XOR = NAND( NAND(a,c), NAND(b,c) )
// (You'll rebuild XOR a different way in Exercise 29.1.)
static int gate_xor(int a, int b) {
    int c = nand(a, b);
    return nand(nand(a, c), nand(b, c));
}

// ---- TRUTH-TABLE PRINTERS ----------------------------------------------------

static void print_unary(const char *name, int (*f)(int)) {
    printf("  %s:  a | out\n", name);
    for (int a = 0; a <= 1; a++) {
        printf("        %d |  %d\n", a, f(a));
    }
    putchar('\n');
}

static void print_binary(const char *name, int (*f)(int, int)) {
    printf("  %s:  a b | out\n", name);
    for (int a = 0; a <= 1; a++) {
        for (int b = 0; b <= 1; b++) {
            printf("        %d %d |  %d\n", a, b, f(a, b));
        }
    }
    putchar('\n');
}

int main(void) {
    printf("=== The one primitive: NAND ===\n");
    print_binary("NAND", nand);

    printf("=== Built from NAND only ===\n");
    print_unary("NOT ", gate_not);
    print_binary("AND ", gate_and);
    print_binary("OR  ", gate_or);
    print_binary("XOR ", gate_xor);

    printf("NAND is *universal*: any boolean function can be expressed using only\n");
    printf("NAND gates. That's why a whole CPU can be built up from this one block.\n");
    return 0;
}
