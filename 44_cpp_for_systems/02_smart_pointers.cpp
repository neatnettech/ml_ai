// Module 44 — Demo 2: smart pointers replace manual malloc/free
//
// Module 30 taught manual heap memory: every malloc needs exactly one free, and a
// missed branch leaks or double-frees. C++ wraps that ownership in a TYPE:
//   - std::unique_ptr<T>  — sole owner; frees automatically when it goes out of
//     scope. MOVE-ONLY: you can transfer ownership, but never copy it (two owners
//     would double-free). This is RAII applied to heap memory.
//   - std::shared_ptr<T>  — shared ownership via a reference count; the last owner
//     to die frees the object.
//
// You never call delete. There is no leak path. Build & run: make run2 (README §2).

#include <cstdio>
#include <memory>
#include <utility>  // std::move

// A small owned resource that announces its own birth and death, so you can SEE
// exactly when the smart pointer frees it.
struct Widget {
    int id;
    explicit Widget(int i) : id(i) { std::printf("    Widget(%d) constructed\n", id); }
    ~Widget() { std::printf("    Widget(%d) destroyed\n", id); }
};

int main() {
    std::printf("=== unique_ptr: sole owner, frees automatically ===\n");
    {
        // make_unique allocates + constructs in one step (the modern replacement for
        // `Widget *w = (Widget*)malloc(...)` then placement-init).
        std::unique_ptr<Widget> a = std::make_unique<Widget>(1);
        std::printf("  a owns Widget(%d)\n", a->id);
        std::printf("  leaving scope...\n");
    }  // <-- no delete: a's destructor frees Widget(1) right here
    std::printf("  (Widget(1) was freed at scope exit — no free() call needed)\n");

    std::printf("\n=== unique_ptr is MOVE-ONLY: ownership transfers ===\n");
    std::unique_ptr<Widget> p = std::make_unique<Widget>(2);
    // auto q = p;            // <-- would NOT compile: copying a unique_ptr is deleted
    std::unique_ptr<Widget> q = std::move(p);  // transfer ownership p -> q
    std::printf("  after std::move: p is %s, q owns Widget(%d)\n",
                p ? "non-null" : "null (empty)", q->id);

    std::printf("\n=== shared_ptr: reference-counted shared ownership ===\n");
    std::shared_ptr<Widget> s1 = std::make_shared<Widget>(3);
    std::printf("  s1 use_count = %ld\n", s1.use_count());
    {
        std::shared_ptr<Widget> s2 = s1;  // copy: both now own Widget(3)
        std::printf("  after copy, use_count = %ld\n", s1.use_count());
        std::printf("  s2 leaving scope...\n");
    }  // s2 dies; count drops back to 1, but the object survives
    std::printf("  after inner scope, use_count = %ld (object still alive)\n",
                s1.use_count());
    std::printf("  main ending — remaining objects freed now:\n");
    // Widget(2) (held by q) and Widget(3) (held by s1) are freed as main returns,
    // in reverse order of declaration. No malloc/free, no leaks.
    return 0;
}
