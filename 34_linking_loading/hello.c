// Module 34 — the four-stages demo input
//
// A deliberately tiny program with ONE macro and ONE call so the four build
// stages (preprocess -> compile -> assemble -> link) each produce something
// small enough to read. See README §1 and `make run1`.

#include <stdio.h>

#define GREETING "hello, linker"

int main(void) {
    puts(GREETING);
    return 0;
}
