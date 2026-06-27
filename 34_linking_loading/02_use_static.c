// Module 34 — Demo 2: link against a STATIC library (libmymath.a)
//
// A static library is just an `ar` archive of .o files. At link time the linker
// COPIES the .o members you actually reference into your executable, then throws
// the archive away. The resulting binary carries mm_gcd/mm_ipow inside it — run
// `nm bin/02_use_static` and you'll see the symbols are DEFINED ('T'), not
// imported ('U'). See README §2 and `make run2`.

#include <stdio.h>
#include "mymath.h"

int main(void) {
    printf("static lib demo\n");
    printf("  mm_gcd(48, 36) = %d\n", mm_gcd(48, 36));
    printf("  mm_ipow(2, 10) = %ld\n", mm_ipow(2, 10));
    return 0;
}
