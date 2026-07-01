/* Exercise 47.1 — Celsius to Fahrenheit  (reference solution, make sol1) */
#include <stdio.h>

double celsius_to_fahrenheit(double c) {
    return c * 9.0 / 5.0 + 32.0;
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
