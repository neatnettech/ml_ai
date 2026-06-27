// Exercise 43.1 — Make a copy bounds-safe
//
// `copy_name` below is the classic vulnerable pattern: it copies an arbitrarily long
// input into a fixed-size buffer with no length check (the `gets`/`strcpy` family of
// bugs). The STUB here is written to stay in-bounds so it runs safely, but it still
// embodies the bug: the copy length is driven by the INPUT, not the DESTINATION.
//
// TODO: rewrite copy_name so it NEVER writes past `dst` (size `dstsz`) and always
// leaves a NUL-terminated string. Then `make ex1` should match `make sol1`.
// Hint: snprintf(dst, dstsz, "%s", src) — or strncpy + manual NUL — works.
//
// Solution: ../solutions/ex1_copy_name.c

#include <stdio.h>
#include <string.h>

#define NAME_CAP 8

static void copy_name(char *dst, size_t dstsz, const char *src) {
    // TODO: make this bounds-safe. Right now it copies min(strlen(src), dstsz-... )
    // in a way that still trusts the input length pattern — replace it with a copy
    // bounded by dstsz that always NUL-terminates.
    //
    // VULNERABLE-STYLE placeholder (kept in-bounds so the stub runs, but it is the
    // wrong shape — fix it):
    size_t n = strlen(src);
    if (n >= dstsz) n = dstsz - 1;   // <- you should not need ad-hoc fixups like this
    memcpy(dst, src, n);
    dst[n] = '\0';
    (void)dstsz;
}

int main(void) {
    char name[NAME_CAP];

    copy_name(name, sizeof name, "bob");
    printf("short input  -> \"%s\"\n", name);

    copy_name(name, sizeof name, "supercalifragilistic");  // way too long
    printf("long input   -> \"%s\"  (must be <= %d chars, NUL-terminated)\n",
           name, NAME_CAP - 1);
    return 0;
}
