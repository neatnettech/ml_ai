// Exercise 44.3 — Rewrite a C-style loop using the STL
//
// Below (commented out) is the kind of code you'd write in C: a fixed array, a
// hand-written bubble sort, and a manual count of elements above a threshold.
// Rewrite `process()` to do the SAME thing with the STL and get identical output:
//   1. put the numbers in a std::vector<int>
//   2. sort it with std::sort
//   3. count how many are > 20 with std::count_if and a lambda
//   4. print the sorted contents with a range-for
//
// Then `make ex3` should match the expected output in README §6. Solution in
// ../solutions/ex3_stl_rewrite.cpp.

#include <cstdio>
#include <vector>
#include <algorithm>  // std::sort, std::count_if

// The C way (for reference — do NOT use this; rewrite with the STL below):
//
//   int a[6] = {42, 7, 19, 3, 25, 11};
//   int n = 6;
//   for (int i = 0; i < n - 1; i++)             // bubble sort
//       for (int j = 0; j < n - 1 - i; j++)
//           if (a[j] > a[j+1]) { int t=a[j]; a[j]=a[j+1]; a[j+1]=t; }
//   int above = 0;
//   for (int i = 0; i < n; i++) if (a[i] > 20) above++;

static void process() {
    // TODO: rewrite the C code above using std::vector, std::sort, std::count_if,
    //       and a range-for. Produce the same output as the solution.
    std::printf("  (not implemented yet)\n");
}

int main() {
    std::printf("=== STL rewrite ===\n");
    process();
    return 0;
}
