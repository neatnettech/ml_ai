// Module 31 — Demo 3: THE PREPROCESSOR (and why it bites)
//
// Before the compiler proper runs, the PREPROCESSOR does pure text substitution:
// it expands #include, replaces #define names, and resolves #if/#ifdef. It does
// NOT understand C — it just pushes tokens around. That ignorance is the source of
// every classic macro bug below. Build & run with: make run3.
//
// Try also:  clang -E 03_preprocessor.c | less   (see the post-preprocessor text)
//            make run3-debug                      (defines DEBUG -> extra output)
// Read alongside README.md §3.

#include <stdio.h>
#include <assert.h>

// ---- 1. Object-like macros: named constants ------------------------------------
// No type, no storage — the token GREETING is literally replaced by the string.
#define GREETING "hello from the preprocessor"
#define MAX_USERS 100

// ---- 2. Function-like macros and their PITFALLS --------------------------------

// PITFALL A: missing parentheses. Text substitution ignores precedence.
//   SQUARE_BAD(2 + 3) -> 2 + 3 * 2 + 3 = 11, not 25.
#define SQUARE_BAD(x)  x * x
// Fixed: parenthesize the WHOLE expansion AND every parameter use.
#define SQUARE_OK(x)  ((x) * (x))

// PITFALL B: double evaluation. The argument's text appears twice, so any side
// effect (a++, a function call, I/O) happens TWICE.
//   MAX(a++, b) increments a one or two times depending on the comparison.
#define MAX(a, b)  ((a) > (b) ? (a) : (b))

// ---- 3. The safe alternative: a static inline function -------------------------
// It evaluates each argument exactly once, respects types and precedence, and is
// still as fast as a macro (the compiler inlines it). Prefer this to MAX above.
static inline int max_int(int a, int b) { return a > b ? a : b; }

int main(void) {
    printf("=== object-like macros ===\n");
    printf("  GREETING  = %s\n", GREETING);
    printf("  MAX_USERS = %d\n", MAX_USERS);

    printf("\n=== pitfall A: SQUARE without parentheses ===\n");
    printf("  SQUARE_BAD(2 + 3) expands to 2 + 3 * 2 + 3 = %d  (WRONG)\n",
           SQUARE_BAD(2 + 3));
    printf("  SQUARE_OK(2 + 3)  = %d  (correct)\n", SQUARE_OK(2 + 3));

    printf("\n=== pitfall B: MAX double-evaluates its arguments ===\n");
    int a = 5, b = 3;
    int m = MAX(a++, b);            // a is read twice: compared, then returned+inc
    printf("  after MAX(a++, b): result=%d, a=%d  (a jumped by 2, surprise!)\n",
           m, a);
    int x = 5, y = 3;
    int sm = max_int(x++, y);       // the inline function reads x++ exactly once
    printf("  after max_int(x++, y): result=%d, x=%d  (a clean single increment)\n",
           sm, x);

    printf("\n=== conditional compilation (#ifdef) ===\n");
#ifdef DEBUG
    printf("  DEBUG build: verbose diagnostics enabled\n");
#else
    printf("  release build: define DEBUG (make run3-debug) for extra output\n");
#endif

    printf("\n=== assert: a checked invariant (compiled out with -DNDEBUG) ===\n");
    int users = 42;
    assert(users <= MAX_USERS);    // aborts with a message if the condition is false
    printf("  assert(users <= MAX_USERS) passed (users=%d)\n", users);

    return 0;
}
