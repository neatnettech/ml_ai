// Module 32 — Demo 3: the calling convention — args in registers, args on the stack,
// and returning a struct
//
// The calling convention is the contract between caller and callee: which registers
// hold which argument, where the return value goes, who saves what. This program
// exercises the interesting cases; view its assembly with `make asm3` and match each
// argument to its register per README.md §3.
//
// arm64 (AAPCS): integer args in x0..x7, return in x0 (small structs in x0/x1).
// x86-64 (System V): integer args in rdi, rsi, rdx, rcx, r8, r9, return in rax.
// Either way, argument 9 and beyond are passed on the STACK.

#include <stdio.h>

// Nine integer arguments: the first eight ride in registers (x0..x7 on arm64),
// and the ninth (i) must be passed on the stack. In `make asm3` you'll see the
// caller store that 9th argument to the stack before the call.
long sum9(long a, long b, long c, long d, long e, long f, long g, long h, long i) {
    return a + b + c + d + e + f + g + h + i;
}

// A small struct returned by value. The ABI says a struct this size (16 bytes) comes
// back in the first two return registers (x0/x1 on arm64, rax/rdx on x86-64) rather
// than via memory — watch for that in the generated asm.
struct point {
    long x;
    long y;
};

struct point make_point(long x, long y) {
    struct point p = {x, y};
    return p;
}

int main(void) {
    printf("sum9(1..9) = %ld  (expected 45)\n",
           sum9(1, 2, 3, 4, 5, 6, 7, 8, 9));

    struct point p = make_point(3, 4);
    printf("make_point(3, 4) = {x=%ld, y=%ld}\n", p.x, p.y);
    return 0;
}
