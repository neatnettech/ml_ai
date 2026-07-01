/* Module 47 — Demo 2: values and decisions.
 *
 * C is statically typed: every variable has a fixed type known at compile time,
 * and each type has a fixed size in bytes. printf uses format specifiers to say
 * how to render a value: %d (int), %f (double), %c (char), %zu (size_t).
 * Then the three control-flow tools you'll use forever: if/else, for, while.
 */
#include <stdio.h>
#include <stdbool.h>

int main(void) {
    /* --- types & sizeof --- */
    int    x     = 7;
    double pi    = 3.14159;
    char   grade = 'A';
    bool   ready = true;

    printf("=== types & sizeof ===\n");
    printf("  int is %zu bytes, double is %zu, char is %zu\n",
           sizeof(int), sizeof(double), sizeof(char));
    printf("  x=%d  pi=%.5f  grade='%c'  ready=%s\n",
           x, pi, grade, ready ? "true" : "false");

    /* --- if/else inside a for loop: FizzBuzz --- */
    printf("=== control flow: first 5 FizzBuzz ===\n");
    printf("  ");
    for (int i = 1; i <= 5; i++) {
        if (i % 15 == 0)      printf("FizzBuzz ");
        else if (i % 3 == 0)  printf("Fizz ");
        else if (i % 5 == 0)  printf("Buzz ");
        else                  printf("%d ", i);
    }
    printf("\n");

    /* --- a while loop --- */
    printf("=== while countdown ===\n");
    printf("  ");
    int n = 3;
    while (n > 0) {
        printf("%d ", n);
        n--;
    }
    printf("liftoff\n");
    return 0;
}
