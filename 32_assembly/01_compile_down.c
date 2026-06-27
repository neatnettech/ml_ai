// Module 32 — Demo 1: Compiling C down to assembly
//
// The compiler turns C into the actual instructions the CPU runs. This file is small
// on purpose so its assembly is readable: a recursive factorial and a summation loop.
// Build & run the C with `make run1`; SEE the native arm64 assembly with `make asm1`
// (which writes 01_compile_down.s next to this file).
//
// Read this alongside README.md §1, where we walk the prologue/epilogue, the
// argument/return registers, and the stack frame in the generated .s.

#include <stdio.h>

// Recursive: each call gets its own stack frame; the base case stops the recursion.
// In the generated asm you'll see the prologue save the return address (x30/lr) and
// frame pointer (x29) so the call can return to its caller.
long factorial(long n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

// A loop: the compiler keeps the accumulator and counter in registers, no stack
// traffic per iteration. Compare the tight loop body in the .s to this source.
long sum_to(long n) {
    long total = 0;
    for (long i = 1; i <= n; i++) {
        total += i;
    }
    return total;
}

int main(void) {
    printf("factorial(5)  = %ld  (expected 120)\n", factorial(5));
    printf("factorial(10) = %ld  (expected 3628800)\n", factorial(10));
    printf("sum_to(100)   = %ld  (expected 5050)\n", sum_to(100));
    return 0;
}
