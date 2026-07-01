// Module 47 — Demo 5: the same ideas, in C++.
//
// C++ is C plus higher-level tools. The same program from demos 3–4 gets
// shorter and safer:
//   std::cout << ...     stream output instead of printf format strings
//   std::string          a real string type — no '\0' bookkeeping, grows itself
//   int&                 a REFERENCE: an alias for a variable, like a pointer
//                        that can't be null and needs no * to use
//   auto                 let the compiler deduce the type
//   std::vector<int>     a growable array that frees its own memory
//
// Same `make`, different compiler under the hood: .cpp builds with
// clang++ -std=c++17.
#include <iostream>
#include <string>
#include <vector>

// a reference parameter mutates the caller's variable — compare add_one(&x) in C
void add_one(int& n) { n += 1; }

int main() {
    std::cout << "=== cout and std::string ===\n";
    std::string name = "Ada";
    std::cout << "  Hello, C++!  name = \"" << name << "\", length "
              << name.size() << "\n";

    std::cout << "=== references: an alias, no pointers needed ===\n";
    int n = 5;
    std::cout << "  before: n = " << n << "\n";
    add_one(n);
    std::cout << "  after add_one(n): n = " << n << "\n";

    std::cout << "=== std::vector: a growable array, freed for you ===\n";
    std::vector<int> v;
    for (int i = 1; i <= 4; i++) v.push_back(i);
    std::cout << "  v =";
    for (auto x : v) std::cout << " " << x;
    std::cout << "  (size " << v.size() << ")\n";

    int total = 0;
    for (auto x : v) total += x;
    std::cout << "  sum via range-for = " << total << "\n";
    return 0;
}
