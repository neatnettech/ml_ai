// Module 44 — Demo 1: references vs pointers, and RAII
//
// C++ adds two things to C that change how you write systems code:
//   - REFERENCES: an alias for an existing object — like a pointer that can't be
//     null and never needs `*` to use. Cleaner pass-by-reference than C's `&`/`*`.
//   - RAII (Resource Acquisition Is Initialization): tie a resource's lifetime to
//     an object's lifetime. The constructor acquires (open file, malloc); the
//     DESTRUCTOR releases (close, free) — and the compiler runs the destructor
//     automatically at scope exit, on every path, even when an exception unwinds.
//
// In C you free/close by hand and a single missed branch leaks. In C++ the cleanup
// is impossible to forget. Build & run: make run1   (read alongside README §1.)

#include <cstdio>

// ---- References vs pointers -------------------------------------------------

// C-style: take the address, dereference to mutate. Caller must write `&x`.
static void add_one_by_pointer(int *p) { *p += 1; }

// C++ reference: `r` IS x (an alias). No `*`, no `&` at the call site, can't be null.
static void add_one_by_reference(int &r) { r += 1; }

// ---- RAII: a FileHandle that wraps FILE* ------------------------------------

// The whole point: opening happens in the constructor, closing in the destructor.
// You can never forget to close it, and it closes the moment the object goes out
// of scope — deterministically, not "sometime later" like a GC.
class FileHandle {
public:
    // Constructor ACQUIRES the resource.
    FileHandle(const char *path, const char *mode) : fp_(std::fopen(path, mode)) {
        if (fp_ != nullptr) {
            std::printf("  [FileHandle] opened %s\n", path);
        }
    }

    // Destructor RELEASES it — runs automatically at scope exit.
    ~FileHandle() {
        if (fp_ != nullptr) {
            std::fclose(fp_);
            std::printf("  [FileHandle] destructor fired -> closed the file\n");
        }
    }

    // A FILE* is a unique resource, so forbid copying (two handles closing the same
    // FILE* would be a double-free-style bug). This is the "rule of zero/three/five"
    // surfacing — we delete what we don't want.
    FileHandle(const FileHandle &) = delete;
    FileHandle &operator=(const FileHandle &) = delete;

    bool ok() const { return fp_ != nullptr; }
    void write_line(const char *s) {
        if (fp_ != nullptr) { std::fprintf(fp_, "%s\n", s); }
    }

private:
    std::FILE *fp_;  // the resource we own
};

int main() {
    std::printf("=== References vs pointers ===\n");
    int x = 5;
    add_one_by_pointer(&x);     // C style: explicit address
    std::printf("  after add_one_by_pointer(&x): x = %d\n", x);
    add_one_by_reference(x);    // C++ style: just pass x; the reference aliases it
    std::printf("  after add_one_by_reference(x): x = %d\n", x);

    int &alias = x;             // alias is another name for x — no separate storage
    alias = 100;
    std::printf("  alias = x; alias = 100; now x = %d (same object)\n", x);

    std::printf("\n=== RAII: deterministic cleanup at scope exit ===\n");
    std::printf("  entering inner scope...\n");
    {
        FileHandle fh("/tmp/m44_raii_demo.txt", "w");  // constructor opens
        if (fh.ok()) {
            fh.write_line("written via an RAII FileHandle");
        }
        std::printf("  ...about to leave the inner scope\n");
    }  // <-- fh's destructor runs HERE, automatically. No manual fclose anywhere.
    std::printf("  back in main: the file is already closed.\n");

    std::printf("\n  In C you'd write fopen ... fclose by hand and every early\n");
    std::printf("  return/error path risks leaking it. RAII makes that impossible.\n");
    return 0;
}
