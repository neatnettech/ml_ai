// Bridge 1 (ctypes) — the kernel in plain C, compiled to a shared library.
//
// This file knows NOTHING about Python. It's an ordinary C function compiled into a
// shared library (libmandel.dylib on macOS, .so on Linux) — exactly the kind of
// dynamic library you built in Module 34. Python's `ctypes` will load this .dylib at
// runtime and call `mandelbrot` directly, passing a pointer to a buffer Python owns.
//
// Built by the Makefile:  clang -O3 -shared -fPIC mandel.c -o libmandel.dylib

#include <stddef.h>

// Compute escape counts into `out` (caller-allocated, width*height ints, row-major).
// Same math and same region as 01_pure_python.py, so the checksums match exactly.
void mandelbrot(int width, int height, int max_iter, int *out) {
    for (int py = 0; py < height; py++) {
        double y0 = -1.25 + 2.5 * py / height;
        for (int px = 0; px < width; px++) {
            double x0 = -2.5 + 3.5 * px / width;
            double x = 0.0, y = 0.0;
            int it = 0;
            while (x * x + y * y <= 4.0 && it < max_iter) {
                double x_new = x * x - y * y + x0;
                y = 2.0 * x * y + y0;
                x = x_new;
                it++;
            }
            out[(size_t)py * width + px] = it;
        }
    }
}
