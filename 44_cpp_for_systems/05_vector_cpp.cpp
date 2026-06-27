// Module 44 — Demo 5: rewrite Module 30's dynamic array in modern C++
//
// Module 30's 05_dynamic_array.c built a vector of ints from raw malloc/realloc/free
// with a manual {data, len, cap} struct, bounds-checking by hand, and exactly one
// free balancing all the growth. Here is the SAME thing, two ways in C++:
//
//   Part A: just use std::vector<int> — the standard library already is that struct,
//           grown and freed for you.
//   Part B: a small RAII templated Vec<T> with the "rule of five" — to show what
//           std::vector does under the hood, now with the destructor (not you)
//           owning the free, and copy/move written explicitly.
//
// Build & run: make run5   (read alongside README §5 — the C-vs-C++ contrast.)

#include <cstdio>
#include <cstddef>
#include <utility>   // std::move, std::swap
#include <vector>

// ---- Part A: the idiomatic answer — std::vector<int> ------------------------

static void part_a_std_vector() {
    std::printf("=== Part A: std::vector<int> (the C struct, done for you) ===\n");
    std::vector<int> v;                 // empty; owns nothing yet
    for (int i = 1; i <= 10; i++) {
        v.push_back(i * i);             // grows internally (amortized O(1))
    }
    std::printf("  size=%zu cap=%zu  (capacity >= size; slack to grow)\n",
                v.size(), v.capacity());
    std::printf("  contents:");
    for (int x : v) { std::printf(" %d", x); }
    std::printf("\n  at(20) is bounds-checked: ");
    try {
        (void)v.at(20);                 // .at() throws on out-of-range (C had none)
    } catch (const std::out_of_range &) {
        std::printf("threw std::out_of_range (C would read garbage)\n");
    }
    // No free anywhere: v's destructor releases the buffer at function exit.
}

// ---- Part B: a hand-rolled RAII Vec<T> with the rule of five -----------------

// When a class owns a raw resource you must define the "rule of five": destructor,
// copy ctor, copy assignment, move ctor, move assignment. std::vector defines all
// of these for you; writing them once shows what that ownership actually entails.
template <typename T>
class Vec {
public:
    Vec() = default;                                  // empty: data_=nullptr

    ~Vec() { delete[] data_; }                        // (1) destructor frees — once

    Vec(const Vec &other)                             // (2) copy constructor: deep copy
        : data_(other.cap_ ? new T[other.cap_] : nullptr),
          len_(other.len_), cap_(other.cap_) {
        for (std::size_t i = 0; i < len_; i++) { data_[i] = other.data_[i]; }
    }

    Vec &operator=(Vec other) {                       // (3) copy assignment via
        swap(*this, other);                           //     copy-and-swap (also
        return *this;                                 //     covers move assignment)
    }

    Vec(Vec &&other) noexcept                         // (4) move constructor: steal
        : data_(other.data_), len_(other.len_), cap_(other.cap_) {
        other.data_ = nullptr;                        // leave source empty but valid
        other.len_ = other.cap_ = 0;
    }
    // (5) move assignment is provided by the by-value operator= above (copy-and-swap).

    void push_back(const T &value) {
        if (len_ == cap_) { grow(); }
        data_[len_++] = value;
    }

    T &operator[](std::size_t i) { return data_[i]; } // unchecked, like C's a[i]

    std::size_t size() const { return len_; }
    std::size_t cap()  const { return cap_; }

    friend void swap(Vec &a, Vec &b) noexcept {
        std::swap(a.data_, b.data_);
        std::swap(a.len_,  b.len_);
        std::swap(a.cap_,  b.cap_);
    }

private:
    void grow() {
        std::size_t new_cap = (cap_ == 0) ? 4 : cap_ * 2;   // 0 -> 4, else double
        T *grown = new T[new_cap];                          // new[] replaces realloc
        for (std::size_t i = 0; i < len_; i++) { grown[i] = data_[i]; }
        delete[] data_;                                     // free old block
        data_ = grown;
        cap_  = new_cap;
        std::printf("    (Vec grew capacity to %zu)\n", cap_);
    }

    T          *data_ = nullptr;  // owned heap buffer
    std::size_t len_  = 0;
    std::size_t cap_  = 0;
};

static void part_b_custom_vec() {
    std::printf("\n=== Part B: a templated RAII Vec<T> (rule of five) ===\n");
    Vec<int> v;
    for (int i = 1; i <= 5; i++) { v.push_back(i * i); }
    std::printf("  size=%zu cap=%zu contents:", v.size(), v.cap());
    for (std::size_t i = 0; i < v.size(); i++) { std::printf(" %d", v[i]); }
    std::printf("\n");

    Vec<int> copy = v;            // deep copy (copy constructor)
    copy.push_back(999);
    std::printf("  after deep copy + push_back(999):\n");
    std::printf("    original size=%zu (unchanged), copy size=%zu\n",
                v.size(), copy.size());

    Vec<int> moved = std::move(v); // steal v's buffer (move constructor)
    std::printf("  after std::move: moved size=%zu, original size=%zu (emptied)\n",
                moved.size(), v.size());
    // All three Vecs free their own buffers at scope exit — no manual free, no leak.
}

int main() {
    part_a_std_vector();
    part_b_custom_vec();
    std::printf("\n  C version: manual realloc, one hand-written free, no bounds\n");
    std::printf("  safety. C++ version: the destructor owns the free; .at() checks\n");
    std::printf("  bounds; copy/move are explicit and leak-free.\n");
    return 0;
}
