// Module 43 — Demo 1: Buffer overflow (EXPLAIN-AND-FIX, runs safely)
//
// White-hat / educational. This program does NOT hijack control flow. It shows the
// ROOT CAUSE of a stack smash — an unbounded copy into a fixed-size buffer — by
// overflowing into an ADJACENT field of the SAME struct, which we can observe
// safely. Then it shows the bounds-checked fix. Build & run with: make run1
//
// Read alongside README.md §1. See the README for how a *real* overflow reaches the
// saved return address and the mitigations (canaries, ASLR, NX/W^X, FORTIFY_SOURCE).

#include <stdio.h>
#include <string.h>

// Two fields side by side. On the stack, writing past `name` runs into `is_admin`.
// (We keep the corruption inside data WE own — there is no return-address hijack and
//  no undefined behaviour reaching past the struct, so the process never crashes.)
typedef struct {
    char name[8];    // fixed-size buffer
    int  is_admin;   // the "adjacent variable" an overflow can clobber
} Account;

// VULNERABLE pattern: copies the whole input regardless of the buffer size.
// We use memcpy with an explicit length that we deliberately keep <= sizeof(Account)
// so the demo stays in-bounds of the struct (observable, no UB, no crash). In real
// vulnerable code this would be strcpy(acc->name, input) with no length at all.
static void set_name_vulnerable(Account *acc, const char *input, size_t input_len) {
    // The bug being illustrated: the copy length comes from the INPUT, not from the
    // destination's capacity. memcpy here writes input_len bytes starting at name[0];
    // anything past byte 8 spills into is_admin.
    memcpy(acc->name, input, input_len);
}

// FIXED pattern: the copy is bounded by the DESTINATION capacity and NUL-terminated.
static void set_name_safe(Account *acc, const char *input) {
    // snprintf never writes more than sizeof(acc->name) bytes and always NUL-terminates.
    snprintf(acc->name, sizeof acc->name, "%s", input);
}

int main(void) {
    printf("=== Buffer overflow: corrupting an ADJACENT field (safe demo) ===\n\n");

    // --- The vulnerable path -------------------------------------------------
    Account a = { .name = "guest", .is_admin = 0 };
    printf("before: name=\"%s\"  is_admin=%d\n", a.name, a.is_admin);

    // Attacker-controlled string. The 8-byte name buffer holds "AAAAAAA" + NUL,
    // and the extra bytes overwrite the adjacent is_admin field with 0x00000001.
    // We size the copy to exactly reach is_admin without going past the struct.
    const unsigned char payload[] = {
        'A','A','A','A','A','A','A','\0',   // fills name[0..7]
        0x01, 0x00, 0x00, 0x00             // lands on is_admin (little-endian 1)
    };
    set_name_vulnerable(&a, (const char *)payload, sizeof payload);

    printf("after : name=\"%s\"  is_admin=%d   <- overflow flipped is_admin!\n",
           a.name, a.is_admin);
    if (a.is_admin) {
        printf("        a 7-char name should NOT grant admin — the copy ran past name[]\n");
    }

    // --- The fixed path ------------------------------------------------------
    printf("\n=== Same input through the bounds-checked version ===\n");
    Account b = { .name = "guest", .is_admin = 0 };
    set_name_safe(&b, "AAAAAAAAAAAAAAAA");   // 16 'A's — far longer than the buffer
    printf("after : name=\"%s\"  is_admin=%d   <- truncated, is_admin untouched\n",
           b.name, b.is_admin);

    printf("\nTakeaway: bound every copy by the DESTINATION size, never the input.\n");
    printf("See README.md §1 for canaries / ASLR / NX / -D_FORTIFY_SOURCE.\n");
    return 0;
}
