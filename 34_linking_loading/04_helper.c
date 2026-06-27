// Module 34 — Demo 4, translation unit #2 (linked with 04_linkage.c)
//
// Shows the other side of internal/external linkage.

#include <stddef.h>

// Refer to the SAME object defined in 04_linkage.c. `extern` says "declared
// here, defined elsewhere" — no new storage, just a name the linker resolves.
extern int g_shared_counter;

// INTERNAL linkage again: this secret() is a DIFFERENT function from the one in
// 04_linkage.c. No duplicate-symbol error, because `static` keeps both private.
static const char *secret(void) {
    return "helper.c's private secret";
}

// EXTERNAL linkage: visible to the linker, called from 04_linkage.c.
void helper_bump(void) {
    g_shared_counter++;
}

// EXTERNAL wrapper so main can observe THIS file's (otherwise hidden) secret().
const char *helper_secret_label(void) {
    return secret();
}
