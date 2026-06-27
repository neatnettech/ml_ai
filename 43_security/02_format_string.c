// Module 43 — Demo 2: Format-string bug (EXPLAIN-AND-FIX, runs safely)
//
// White-hat / educational. `printf(user_input)` treats attacker data as a FORMAT
// STRING — if it contains conversions like %x or %n, printf reads (or writes!) memory
// the attacker never passed as arguments. This demo shows the bug SAFELY (it prints a
// benign literal as if it were tainted, and never feeds an attacker %n) and then the
// one-line fix. Build & run with: make run2.  Read alongside README.md §2.

#include <stdio.h>

// VULNERABLE: the caller's string is used as the format. If it contained "%x %x %x"
// printf would walk the stack/registers and leak values; "%n" would WRITE to memory.
static void log_vulnerable(const char *user_input) {
    // For the demo we pass a benign string, so nothing is leaked. The point is the
    // SHAPE of the call: there is no fixed format string controlling the conversions.
    // We locally silence -Wformat-security so the file builds warning-clean; in real
    // code this diagnostic is exactly what you want — do NOT suppress it.
#if defined(__clang__) || defined(__GNUC__)
#  pragma GCC diagnostic push
#  pragma GCC diagnostic ignored "-Wformat-security"
#  pragma GCC diagnostic ignored "-Wformat-nonliteral"
#endif
    printf(user_input);   // BUG (shown deliberately; input here is harmless)
#if defined(__clang__) || defined(__GNUC__)
#  pragma GCC diagnostic pop
#endif
    printf("\n");
}

// FIXED: the format string is a constant we control; user data is just a %s argument.
static void log_safe(const char *user_input) {
    printf("%s\n", user_input);   // user data can never introduce conversions
}

int main(void) {
    printf("=== Format-string bug: user data must never BE the format ===\n\n");

    // A normal, benign message. Note: it contains NO % conversions, so even the
    // vulnerable call behaves identically here — that's the trap. The code is wrong
    // even when today's input happens to be safe.
    const char *benign = "user 'alice' logged in";

    printf("vulnerable call, benign input : ");
    log_vulnerable(benign);
    printf("safe call,       benign input : ");
    log_safe(benign);

    // Demonstrate the DIFFERENCE without weaponising it: a string that *contains*
    // a percent sign. The safe version prints it literally; the vulnerable version
    // would (mis)interpret it as the start of a conversion. We only ever send this
    // through the SAFE path so no out-of-bounds varargs read happens.
    printf("\nA string with a literal '%%' through the SAFE path:\n  ");
    log_safe("discount is 50% off (note the percent sign)");

    printf("\nWhy the vulnerable form is dangerous (NOT executed here):\n");
    printf("  - \"%%x %%x %%x\" -> printf reads values never passed -> INFO LEAK\n");
    printf("  - \"%%n\"        -> printf WRITES the byte-count to a pointer -> MEMORY WRITE\n");
    printf("\nFix: always pass a constant format; put user data in a %%s argument.\n");
    printf("Compilers help: clang -Wformat-security flags printf(non_literal).\n");
    return 0;
}
