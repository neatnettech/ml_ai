// SOLUTION 31.3 — a correct MIN macro vs the safer inline function

#include <stdio.h>

// (a) Fully parenthesized macro: every parameter and the whole expression are
//     wrapped, so it behaves under operator precedence and with odd arguments.
//     It STILL double-evaluates its arguments — that's inherent to macros.
#define MIN(a, b) ((a) < (b) ? (a) : (b))

// (b) The safe twin: each argument is evaluated exactly once (it's a real function
//     call), and it is type-checked. `inline` lets the compiler emit it as fast as
//     the macro. Prefer this in real code.
static inline int min_int(int a, int b) { return a < b ? a : b; }

int main(void) {
    printf("MIN(3, 7)     = %d  (expected 3)\n", MIN(3, 7));
    printf("min_int(3, 7) = %d  (expected 3)\n", min_int(3, 7));

    // Show the double-evaluation hazard. With MIN, a++ expands twice; because the
    // left side (5) is the smaller, it is evaluated in the comparison AND returned,
    // incrementing a twice -> a ends at 7.
    int a = 5;
    int viaMacro = MIN(a++, 100);
    printf("\nMIN(a++, 100) = %d, a = %d   <- macro bumped a TWICE\n", viaMacro, a);

    // The function takes b++ as a single evaluated argument -> b ends at 6.
    int b = 5;
    int viaFunc = min_int(b++, 100);
    printf("min_int(b++,100) = %d, b = %d  <- function bumped b ONCE\n",
           viaFunc, b);
    return 0;
}
