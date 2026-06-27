// Module 44 — Demo 4: the Standard Template Library (STL)
//
// In Modules 30/38 you hand-built vectors, strings, hash maps, and sorts. The STL
// ships all of them, tuned and tested, as templates:
//   - std::vector<T>        — the growable array from Module 30, done for you
//   - std::string           — NUL-handling, growth, concat — no manual char arrays
//   - std::unordered_map<K,V> — the hash map from Module 38, O(1) average lookup
//   - <algorithm>           — sort, find_if, ... that work on any container via
//                             iterators, often driven by a lambda (an inline function)
//
// Build & run: make run4   (read alongside README §4.)

#include <cstdio>
#include <vector>
#include <string>
#include <unordered_map>
#include <algorithm>  // std::sort, std::find_if

int main() {
    std::printf("=== std::vector<int>: growable array, no malloc/realloc ===\n");
    std::vector<int> v;             // starts empty; grows itself
    for (int i = 1; i <= 6; i++) {
        v.push_back(i * i);         // append; the vector reallocs internally
    }
    std::printf("  size=%zu, contents:", v.size());
    for (int x : v) { std::printf(" %d", x); }  // range-for over the container
    std::printf("\n");

    std::printf("\n=== <algorithm>: sort + find_if with a lambda ===\n");
    std::vector<int> nums = {42, 7, 19, 3, 25, 11};
    std::sort(nums.begin(), nums.end());        // ascending sort, one line
    std::printf("  sorted:");
    for (int x : nums) { std::printf(" %d", x); }
    std::printf("\n");
    // find_if returns an iterator to the first element matching the predicate.
    // The [](int n){...} is a LAMBDA — an anonymous function written inline.
    auto it = std::find_if(nums.begin(), nums.end(),
                           [](int n) { return n > 15; });
    if (it != nums.end()) {
        std::printf("  first element > 15 is %d\n", *it);
    }

    std::printf("\n=== std::string: real strings, no '\\0' bookkeeping ===\n");
    std::string greeting = "hello";
    greeting += ", systems world";                 // concatenation just works
    std::printf("  \"%s\" (length %zu)\n", greeting.c_str(), greeting.size());

    std::printf("\n=== std::unordered_map: the Module 38 hash map, for free ===\n");
    std::unordered_map<std::string, int> counts;
    std::vector<std::string> words = {"c", "cpp", "c", "rust", "cpp", "c"};
    for (const std::string &w : words) {
        counts[w]++;               // default-constructs 0 on first sight, then ++
    }
    // Iterate keys in a stable order for reproducible output (maps are unordered).
    for (const std::string &key : {std::string("c"), std::string("cpp"),
                                   std::string("rust")}) {
        std::printf("  %-4s -> %d\n", key.c_str(), counts[key]);
    }

    std::printf("\n  Every container above frees its own memory (RAII). The STL is\n");
    std::printf("  most of Modules 30 and 38, type-safe and zero-cost, out of the box.\n");
    return 0;
}
