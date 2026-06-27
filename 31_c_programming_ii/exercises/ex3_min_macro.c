// Exercise 31.3 — A correct MIN macro, and its safer inline-function twin
//
// (a) Write the function-like macro MIN(a,b) with FULL parenthesization:
//        wrap each parameter AND the whole expression in parentheses, so it
//        survives being embedded in a larger expression and odd arguments.
// (b) Write min_int(a,b) as a `static inline` function — the safe version that
//        evaluates each argument exactly once.
// (c) The main() below feeds a side-effecting argument (a++) to BOTH so you can
//        SEE the macro double-evaluate while the function does not.
//
// Build & run:  make ex3     Reference: ../solutions/ex3_min_macro.c

#include <stdio.h>

// TODO (a): define MIN(a,b) with full parenthesization, e.g.
//   #define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MIN(a, b) 0   /* TODO: replace 0 with the real parenthesized macro */

// TODO (b): define the safe inline function.
static inline int min_int(int a, int b) {
    (void)a; (void)b;   // remove once implemented
    return 0;           // TODO: return the smaller of a and b
}

int main(void) {
    printf("MIN(3, 7)     = %d  (expected 3)\n", MIN(3, 7));
    printf("min_int(3, 7) = %d  (expected 3)\n", min_int(3, 7));

    // The double-evaluation demonstration: a++ appears twice after macro expansion.
    int a = 5;
    int viaMacro = MIN(a++, 100);   // a is read, compared, then maybe read again
    printf("\nMIN(a++, 100) = %d, a = %d   <- macro may bump a twice\n", viaMacro, a);

    int b = 5;
    int viaFunc = min_int(b++, 100);
    printf("min_int(b++,100) = %d, b = %d  <- function bumps b exactly once\n",
           viaFunc, b);
    return 0;
}
