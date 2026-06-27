// SOLUTION 44.1 — An RAII buffer wrapper

#include <cstdio>
#include <cstddef>

class Buffer {
public:
    explicit Buffer(std::size_t n) : data_(new int[n]), size_(n) {
        std::printf("  [Buffer] allocated %zu ints\n", n);
    }

    ~Buffer() {
        delete[] data_;
        std::printf("  [Buffer] freed %zu ints\n", size_);
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
