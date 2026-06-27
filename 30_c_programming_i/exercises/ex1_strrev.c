// Exercise 30.1 — Reverse a string in place with two pointers
//
// Implement `my_strrev` so it reverses the characters of `s` IN PLACE (no extra
// buffer), using two pointers that walk toward each other. Then `make ex1` should
// match the expected output in README.md §6. Solution in ../solutions/ex1_strrev.c.

#include <stdio.h>
#include <string.h>

void my_strrev(char *s) {
    // TODO: set `left` to the first char and `right` to the last char (NOT the
    // '\0' — that's strlen(s) - 1). While left < right, swap *left and *right,
    // then left++ and right--. The '\0' stays at the end.
    (void)s;  // remove this line once you use s
}

int main(void) {
    char a[] = "pointers";
    char b[] = "C";
    char c[] = "";  // empty string: must stay empty, must not crash
    my_strrev(a);
    my_strrev(b);
    my_strrev(c);
    printf("reversed: \"%s\"\n", a);
    printf("reversed: \"%s\"\n", b);
    printf("reversed: \"%s\" (empty stays empty)\n", c);
    return 0;
}
