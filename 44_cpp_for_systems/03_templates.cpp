// Module 44 — Demo 3: templates — compile-time generics
//
// C's only generic tool is void* (think qsort): you lose the type, cast everywhere,
// and the compiler can't check you. C++ TEMPLATES let you write code once and have
// the compiler stamp out a type-checked copy for each concrete type you use it with.
// It's COMPILE-TIME polymorphism: no runtime cost, full type safety.
//
//   - function template:  max_of<T>(a, b)
//   - class template:     Stack<T>
//
// Build & run: make run3   (read alongside README §3.)

#include <cstdio>
#include <stdexcept>
#include <initializer_list>  // for the brace-list range-for below

// ---- Function template ------------------------------------------------------

// One definition; the compiler instantiates max_of<int>, max_of<double>, ... on
// demand. Contrast C, where you'd need a macro (no type safety) or one function
// per type.
template <typename T>
T max_of(T a, T b) {
    return (a > b) ? a : b;
}

// ---- Class template: a generic fixed-capacity Stack<T> ----------------------

template <typename T, int Capacity = 8>
class Stack {
public:
    bool empty() const { return size_ == 0; }
    int  size()  const { return size_; }

    void push(const T &value) {
        if (size_ >= Capacity) {
            throw std::overflow_error("stack full");
        }
        data_[size_++] = value;
    }

    T pop() {
        if (empty()) {
            throw std::underflow_error("stack empty");
        }
        return data_[--size_];
    }

private:
    T   data_[Capacity];  // storage is sized at compile time
    int size_ = 0;
};

int main() {
    std::printf("=== Function template: one max_of for every type ===\n");
    std::printf("  max_of<int>(3, 9)        = %d\n",  max_of<int>(3, 9));
    std::printf("  max_of<double>(2.5, 1.5) = %.1f\n", max_of<double>(2.5, 1.5));
    // Template argument can be deduced from the arguments — no <char> needed:
    std::printf("  max_of('a', 'z') deduced = %c\n",  max_of('a', 'z'));

    std::printf("\n=== Class template: Stack<int> ===\n");
    Stack<int> s;
    for (int v : {10, 20, 30}) {
        s.push(v);
        std::printf("  push(%d), size=%d\n", v, s.size());
    }
    while (!s.empty()) {
        std::printf("  pop -> %d\n", s.pop());
    }

    std::printf("\n=== The SAME Stack template, now holding doubles ===\n");
    Stack<double> sd;
    sd.push(1.5);
    sd.push(2.5);
    std::printf("  pop -> %.1f\n", sd.pop());
    std::printf("  pop -> %.1f\n", sd.pop());

    std::printf("\n  Each Stack<T> is a distinct, fully type-checked class the\n");
    std::printf("  compiler generated for us — no void*, no casts, no runtime cost.\n");
    return 0;
}
