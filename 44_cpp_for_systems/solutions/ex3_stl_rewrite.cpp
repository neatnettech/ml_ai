// SOLUTION 44.3 — Rewrite a C-style loop using the STL

#include <cstdio>
#include <vector>
#include <algorithm>  // std::sort, std::count_if

static void process() {
    std::vector<int> nums = {42, 7, 19, 3, 25, 11};   // (1) container, not a raw array

    std::sort(nums.begin(), nums.end());              // (2) one-line sort

    long above = std::count_if(nums.begin(), nums.end(),
                               [](int n) { return n > 20; });  // (3) lambda predicate

    std::printf("  sorted:");
    for (int n : nums) { std::printf(" %d", n); }     // (4) range-for
    std::printf("\n  count > 20 = %ld\n", above);
}

int main() {
    std::printf("=== STL rewrite ===\n");
    process();
    return 0;
}
