// Exercise 34.1 — the MAIN translation unit (links against libtemp.a).
//
// As given, this is the ORIGINAL single-file program: c_to_f is defined right
// here next to main. Your task is to MOVE the definition out into the library
// (ex1_celsius_lib.c + ex1_celsius.h) so that this file only DECLARES it via the
// header and CALLS it — the linker then joins main.o with libtemp.a.
//
// TODO: delete the local definition below and `#include "ex1_celsius.h"` instead.

#include <stdio.h>

// TODO: remove this definition once it lives in the library; include the header.
double c_to_f(double celsius) {
    return celsius * 9.0 / 5.0 + 32.0;
}

int main(void) {
    double samples[] = {0.0, 37.0, 100.0};
    for (size_t i = 0; i < sizeof samples / sizeof *samples; i++) {
        printf("  %6.1f C = %6.1f F\n", samples[i], c_to_f(samples[i]));
    }
    return 0;
}
