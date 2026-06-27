// Exercise 34.2 — trigger and read an "undefined symbol" linker error, then fix.
//
// This file DECLARES `triple` and CALLS it, but never DEFINES it. The compiler
// is happy — a declaration is a promise, and main() compiles fine. The LINKER
// is not: nothing provides the code for `triple`, so it aborts with
//
//   Undefined symbols for architecture arm64:
//     "_triple", referenced from:
//         _main in ex2_undefined-XXXX.o
//   ld: symbol(s) not found for architecture arm64
//
// (On Linux/ELF the wording is: "undefined reference to `triple'".)
//
// `make ex2` is EXPECTED TO FAIL on this file — that is the whole point. Read the
// message, note the leading underscore Mach-O adds to C names (_triple), then:
//
// TODO: make it link by DEFINING triple below, e.g.
//          int triple(int x) { return x * 3; }
//       The fixed version is solutions/ex2_undefined.c (`make sol2`).

#include <stdio.h>

// Declaration only — a promise the linker will try (and fail) to keep.
int triple(int x);

int main(void) {
    printf("triple(7) = %d\n", triple(7));
    return 0;
}

// TODO: define triple here to fix the undefined-symbol error.
