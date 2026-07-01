// Exercise 47.3 — A little stack class  (make ex3)
//
// Finish the IntStack class: it's a last-in-first-out stack backed by a
// std::vector<int>. Implement push, pop, and size. `back()` reads the last
// element; `pop_back()` removes it. Check against `make sol3`.
#include <iostream>
#include <vector>

class IntStack {
public:
    void push(int v) {
        // TODO: add v to the top of the stack
        (void)v;   // remove once you use v
    }

    int pop() {
        // TODO: remove and return the top element
        return 0;
    }

    int size() const {
        // TODO: return how many elements are on the stack
        return 0;
    }

private:
    std::vector<int> data_;
};

int main() {
    IntStack s;
    s.push(10);
    s.push(20);
    s.push(30);
    std::cout << "=== IntStack ===\n";
    std::cout << "  push 10, 20, 30  -> size " << s.size() << "\n";
    std::cout << "  pop -> " << s.pop() << "\n";
    std::cout << "  pop -> " << s.pop() << "\n";
    std::cout << "  size now " << s.size() << "\n";
    return 0;
}
