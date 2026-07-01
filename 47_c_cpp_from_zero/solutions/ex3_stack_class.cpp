// Exercise 47.3 — A little stack class  (reference solution, make sol3)
#include <iostream>
#include <vector>

class IntStack {
public:
    void push(int v) { data_.push_back(v); }

    int pop() {
        int top = data_.back();
        data_.pop_back();
        return top;
    }

    int size() const { return static_cast<int>(data_.size()); }

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
