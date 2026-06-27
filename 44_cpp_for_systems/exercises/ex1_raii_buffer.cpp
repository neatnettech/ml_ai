// Exercise 44.1 — An RAII buffer wrapper
//
// Build a class `Buffer` that owns a heap allocation: its CONSTRUCTOR allocates
// `n` ints with `new[]`, and its DESTRUCTOR frees them with `delete[]`. Because the
// destructor runs automatically at scope exit, you never call delete yourself — and
// the "[Buffer] freed N ints" line should print when `b` leaves main's scope.
//
// Then `make ex1` should match the expected output in README §6. Solution in
// ../solutions/ex1_raii_buffer.cpp.

#include <cstdio>
#include <cstddef>

class Buffer {
public:
    // TODO: constructor — allocate `n` ints into data_, store n in size_, and
    //       printf("  [Buffer] allocated %zu ints\n", n);
    explicit Buffer(std::size_t n) {
        (void)n;  // remove once implemented
    }

    // TODO: destructor — delete[] the buffer and
    //       printf("  [Buffer] freed %zu ints\n", size_);
    ~Buffer() {
    }

    void set(std::size_t i, int value) { data_[i] = value; }
    int  get(std::size_t i) const { return data_[i]; }
    std::size_t size() const { return size_; }

private:
    int        *data_ = nullptr;
    std::size_t size_ = 0;
};

int main() {
    std::printf("=== RAII buffer ===\n");
    {
        Buffer b(4);
        for (std::size_t i = 0; i < b.size(); i++) { b.set(i, (int)(i * 10)); }
        std::printf("  contents:");
        for (std::size_t i = 0; i < b.size(); i++) { std::printf(" %d", b.get(i)); }
        std::printf("\n  leaving scope (destructor should fire next)...\n");
    }  // <-- b's destructor runs here
    std::printf("  back in main: buffer already freed.\n");
    return 0;
}
