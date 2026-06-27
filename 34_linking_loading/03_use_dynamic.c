// Module 34 — Demo 3: link against a DYNAMIC library (libmymath.dylib)
//
// A dynamic library is NOT copied in. The linker records a dependency ("I need
// libmymath.dylib, and from it the symbols mm_gcd/mm_ipow"). At RUN time the
// dynamic loader (dyld on macOS, ld.so on Linux) maps the library into the
// process and binds the symbols. Run `nm bin/03_use_dynamic` and mm_gcd shows
// as 'U' (undefined / imported); `otool -L bin/03_use_dynamic` lists the .dylib
// as a load-time dependency. See README §3 and `make run3`.

#include <stdio.h>
#include "mymath.h"

int main(void) {
    printf("dynamic lib demo\n");
    printf("  mm_gcd(1071, 462) = %d\n", mm_gcd(1071, 462));
    printf("  mm_ipow(3, 4)     = %ld\n", mm_ipow(3, 4));
    return 0;
}
