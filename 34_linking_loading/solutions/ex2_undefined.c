// SOLUTION 34.2 — the FIXED version: triple is now DEFINED, so the linker
// resolves the reference and the program links and runs. See README §6 for a
// walk-through of the original error message.

#include <stdio.h>

int triple(int x);   // declaration (could also live in a header)

int main(void) {
    printf("triple(7) = %d\n", triple(7));
    return 0;
}

// The definition the linker was missing.
int triple(int x) {
    return x * 3;
}
