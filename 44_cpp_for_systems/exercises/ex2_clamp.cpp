// Exercise 44.2 — A generic clamp() function template
//
// Implement `template <typename T> T clamp(T v, T lo, T hi)` that returns lo if
// v < lo, hi if v > hi, and v otherwise. Because it's a template, the SAME code
// must work for int and double (and anything with operator<). Use it with both.
//
// Then `make ex2` should match the expected output in README §6. Solution in
// ../solutions/ex2_clamp.cpp.

#include <cstdio>

// TODO: implement the clamp function template.
//   - return lo when v < lo
//   - return hi when v > hi
//   - otherwise return v
template <typename T>
T clamp(T v, T lo, T hi) {
    (void)lo; (void)hi;  // remove once implemented
    return v;            // replace with the real logic
}

int main() {
    std::printf("=== clamp<int> ===\n");
    std::printf("  clamp(5, 0, 10)   = %d\n",  clamp(5, 0, 10));
    std::printf("  clamp(-3, 0, 10)  = %d\n",  clamp(-3, 0, 10));
    std::printf("  clamp(99, 0, 10)  = %d\n",  clamp(99, 0, 10));

    std::printf("=== clamp<double> (same template) ===\n");
    std::printf("  clamp(0.5, 0.0, 1.0)  = %.1f\n", clamp(0.5, 0.0, 1.0));
    std::printf("  clamp(2.5, 0.0, 1.0)  = %.1f\n", clamp(2.5, 0.0, 1.0));
    return 0;
}
