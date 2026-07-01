// Module 47 — Demo 6: your own type that cleans up after itself.
//
// A class bundles data with the functions that operate on it. Two special
// members run automatically:
//   constructor  runs when an object is created (set up / acquire resources)
//   destructor   runs when it goes out of scope (release / clean up)
// This pattern is called RAII. Compare demo 4: in C you must remember to call
// free(); here the destructor fires on its own at scope exit, on every path.
//
// Templates let one definition work for many types — a taste of what powers
// std::vector. For smart pointers, the STL in depth, and the rule of five, see
// Module 44 — C++ for Systems.
#include <iostream>

class Counter {
public:
    Counter() : count_(0) {
        std::cout << "  [Counter] constructed (count=0)\n";
    }
    ~Counter() {
        std::cout << "  [Counter] destructed at count=" << count_
                  << "  (no free() needed — the destructor ran automatically)\n";
    }
    void tick() {
        ++count_;
        std::cout << "  tick -> " << count_ << "\n";
    }

private:
    int count_;
};

// one definition, any type the compiler can compare with >
template <typename T>
T max_of(T a, T b) { return a > b ? a : b; }

int main() {
    std::cout << "=== a class with RAII (constructor/destructor) ===\n";
    {
        Counter c;
        c.tick();
        c.tick();
        std::cout << "  leaving scope...\n";
    }  // c's destructor fires here, automatically

    std::cout << "=== a tiny template: one max_of for any type ===\n";
    std::cout << "  max_of(3, 9)     = " << max_of(3, 9) << "\n";
    std::cout << "  max_of(2.5, 1.5) = " << max_of(2.5, 1.5) << "\n";
    return 0;
}
