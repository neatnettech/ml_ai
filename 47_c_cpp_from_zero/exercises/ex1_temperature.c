/* Exercise 47.1 — Celsius to Fahrenheit  (make ex1)
 *
 * Implement celsius_to_fahrenheit below, then run `make ex1`. The table should
 * print the Fahrenheit value for each Celsius input. Check `make sol1`.
 *
 * Formula: F = C * 9/5 + 32   (use 9.0/5.0 so it's floating-point division!)
 */
#include <stdio.h>

double celsius_to_fahrenheit(double c) {
    /* TODO: return the Fahrenheit equivalent of c */
    (void)c;      /* remove this line once you use c */
    return 0.0;
}

int main(void) {
    double inputs[] = {0.0, 20.0, 37.0, 100.0};
    int n = (int)(sizeof(inputs) / sizeof(inputs[0]));

    printf("=== C -> F table ===\n");
    for (int i = 0; i < n; i++) {
        printf("  %4.0fC = %6.1fF\n", inputs[i], celsius_to_fahrenheit(inputs[i]));
    }
    return 0;
}
