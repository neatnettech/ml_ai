/* Module 47 — Demo 1: your first program and how it gets built.
 *
 * A C program is text. The compiler (clang) turns it into a native executable
 * your CPU runs directly — no interpreter, unlike Python. `make run1` compiles
 * this file with `clang -std=c11 -o bin/01_hello 01_hello.c` and runs it.
 *
 *   #include <stdio.h>   pulls in the standard I/O declarations (printf).
 *   int main(void)       is where every C program starts.
 *   return 0;            tells the OS "exited successfully" (non-zero = error).
 */
#include <stdio.h>

int main(void) {
    printf("Hello, C!\n");
    printf("This program was compiled to a native executable.\n");
    return 0;
}
