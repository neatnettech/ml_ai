// SOLUTION 30.1 — Reverse a string in place with two pointers

#include <stdio.h>
#include <string.h>

void my_strrev(char *s) {
    if (*s == '\0') return;           // empty string: nothing to do
    char *left  = s;                  // first character
    char *right = s + strlen(s) - 1;  // last character (before the '\0')
    while (left < right) {            // walk inward until they meet/cross
        char tmp = *left;
        *left = *right;
        *right = tmp;
        left++;
        right--;
    }
}

int main(void) {
    char a[] = "pointers";
    char b[] = "C";
    char c[] = "";
    my_strrev(a);
    my_strrev(b);
    my_strrev(c);
    printf("reversed: \"%s\"\n", a);
    printf("reversed: \"%s\"\n", b);
    printf("reversed: \"%s\" (empty stays empty)\n", c);
    return 0;
}
