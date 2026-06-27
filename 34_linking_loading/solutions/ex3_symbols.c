// SOLUTION 34.3 — same program; the answers from inspecting it on macOS/arm64:
//
//   nm bin/sol_ex3_symbols (abridged; addresses vary per build):
//     0000000100000460 T _my_square      <- 'T': DEFINED in this binary (text)
//                      U _printf          <- 'U': UNDEFINED, imported from libc
//
//   otool -L bin/sol_ex3_symbols:
//     /usr/lib/libSystem.B.dylib          <- supplies printf via dyld at run time
//
// Answers:
//   1. _my_square is 'T' (defined here; Mach-O prefixes C names with '_').
//   2. _printf is 'U' (imported; resolved at load time by dyld).
//   3. /usr/lib/libSystem.B.dylib (macOS bundles the C library here; on Linux it
//      would be libc.so.6 reported by `ldd`).

#include <stdio.h>

int my_square(int x) {
    return x * x;
}

int main(void) {
    printf("my_square(9) = %d\n", my_square(9));
    return 0;
}
