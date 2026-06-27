// Exercise 34.1 — split a single-file program into a library + main.
//
// You are given ex1_celsius.c, which jams a conversion function and main() into
// one file. Your job: pull the function into a LIBRARY (this header declares it,
// ex1_celsius_lib.c defines it), build it into an archive libtemp.a, and have a
// thin main link against it. The Makefile target `make ex1` already does the
// build steps; you just fill in the source split.
//
// TODO: declare the function `double c_to_f(double celsius);` here, between the
//       include guard, then DEFINE it in ex1_celsius_lib.c (not in the main).

#ifndef EX1_CELSIUS_H
#define EX1_CELSIUS_H

// TODO: declare c_to_f here, e.g.  double c_to_f(double celsius);

// Placeholder so the as-given files compile with zero warnings before you start.
// Delete it once you add the real declaration above.
void ex1_todo(void);

#endif  // EX1_CELSIUS_H
