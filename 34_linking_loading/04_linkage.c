// Module 34 — Demo 4: internal vs external linkage
//
// "Linkage" decides whether a name in one translation unit refers to the SAME
// entity as a name in another. The linker only ever sees names with EXTERNAL
// linkage; names with INTERNAL linkage are private to their .c file and never
// reach the linker's symbol table. See README §4 and `make run4`.
//
// This file (TU #1) is linked with 04_helper.c (TU #2):
//   - g_shared_counter : file-scope, EXTERNAL  -> one object shared by both TUs
//   - secret()         : file-scope `static`, INTERNAL -> private to THIS file;
//                        04_helper.c has its OWN unrelated secret()
//   - helper_bump()    : EXTERNAL, defined in 04_helper.c, called from here

#include <stdio.h>

// EXTERNAL linkage: a single definition lives here; 04_helper.c reaches it via
// `extern int g_shared_counter;`. Both files read and write the SAME variable.
int g_shared_counter = 0;

// INTERNAL linkage: `static` at file scope hides this name from the linker.
// 04_helper.c defines a function ALSO named secret() with no conflict, because
// neither name is visible outside its own translation unit.
static const char *secret(void) {
    return "main.c's private secret";
}

// Declared in 04_helper.c (EXTERNAL). The compiler trusts this promise; the
// linker resolves it against the definition in the other object file.
void helper_bump(void);
const char *helper_secret_label(void);

int main(void) {
    printf("internal vs external linkage\n");

    printf("  before: g_shared_counter = %d\n", g_shared_counter);
    g_shared_counter++;          // bumped here
    helper_bump();               // bumped in the OTHER translation unit
    printf("  after main++ and helper_bump(): g_shared_counter = %d\n",
           g_shared_counter);     // 2 -> the variable is shared

    // Two same-named static functions coexist: each TU sees only its own.
    printf("  this file's secret(): %s\n", secret());
    printf("  helper's  secret(): %s\n", helper_secret_label());
    return 0;
}
