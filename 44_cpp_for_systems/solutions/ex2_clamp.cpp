// SOLUTION 44.2 — A generic clamp() function template

#include <cstdio>

template <typename T>
T clamp(T v, T lo, T hi) {
    if (v < lo) { return lo; }
    if (v > hi) { return hi; }
    return v;
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
