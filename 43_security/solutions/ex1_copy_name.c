// SOLUTION 43.1 — Make a copy bounds-safe

#include <stdio.h>
#include <string.h>

#define NAME_CAP 8

// Bounded by the DESTINATION capacity, always NUL-terminated, regardless of input.
static void copy_name(char *dst, size_t dstsz, const char *src) {
    if (dstsz == 0) return;
    // snprintf writes at most dstsz-1 chars + a guaranteed NUL terminator.
    snprintf(dst, dstsz, "%s", src);
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
