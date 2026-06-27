// Exercise 34.3 — read a binary's symbols with nm / otool.
//
// This program defines its own function (my_square) AND calls library functions
// it does NOT define (printf, from the C library). After it builds, inspect it:
//
//     nm   bin/ex_ex3_symbols      # symbol table: T = defined here, U = imported
//     otool -L bin/ex_ex3_symbols  # shared libraries loaded at run time
//
// `make ex3` builds it and prints these two listings for you.
//
// TODO (no code change needed — answer in this comment after running `make ex3`):
//   1. Which symbol shows as 'T' (text/defined in THIS binary)?  ........
//   2. Which symbol(s) show as 'U' (undefined / imported from elsewhere)? ......
//   3. Which dylib does `otool -L` say supplies printf?           ........
//
// Linux/ELF: use `readelf -s` (or `nm`) and `ldd` instead; imported symbols
// are marked UND and the C library is libc.so.6.

#include <stdio.h>

int my_square(int x) {
    return x * x;
}

int main(void) {
    printf("my_square(9) = %d\n", my_square(9));
    return 0;
}
