// SOLUTION 34.1 — main: only DECLARES (via the header) and CALLS; the linker
// resolves c_to_f against libtemp.a built from ex1_celsius_lib.c.

#include <stdio.h>
#include <stddef.h>
#include "ex1_celsius.h"

int main(void) {
    double samples[] = {0.0, 37.0, 100.0};
    for (size_t i = 0; i < sizeof samples / sizeof *samples; i++) {
        printf("  %6.1f C = %6.1f F\n", samples[i], c_to_f(samples[i]));
    }
    return 0;
}
