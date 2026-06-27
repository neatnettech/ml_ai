// Module 30 — Demo 3: C strings are NUL-terminated char arrays
//
// C has no string type. A "string" is just a char array whose end is marked by a
// '\0' (the NUL byte, value 0). Every standard string function relies on that
// terminator. We reimplement strlen/strcpy/strcmp with pointers to see exactly
// how — including the off-by-one for the '\0'. Build & run with: make run3
//
// Read top to bottom alongside README.md §3.

#include <stdio.h>

// strlen: walk until the NUL. The length does NOT count the terminator.
static size_t my_strlen(const char *s) {
    const char *p = s;
    while (*p != '\0') {  // stop AT the terminator, don't count it
        p++;
    }
    return (size_t)(p - s);  // pointer difference = number of chars before '\0'
}

// strcpy: copy src into dst INCLUDING the '\0'. Caller must ensure dst is big
// enough (at least my_strlen(src)+1 bytes — the +1 is the off-by-one for '\0').
// Returns dst, like the real strcpy.
static char *my_strcpy(char *dst, const char *src) {
    char *out = dst;
    while ((*dst = *src) != '\0') {  // assign, THEN test the copied byte
        dst++;
        src++;
    }
    // The loop already copied the terminating '\0' (that's the iteration that
    // made the condition false), so dst is fully terminated.
    return out;
}

// strcmp: compare byte by byte. Return <0, 0, >0 like the standard one.
static int my_strcmp(const char *a, const char *b) {
    while (*a != '\0' && *a == *b) {  // advance while equal and not at the end
        a++;
        b++;
    }
    // Compare as unsigned char (the standard's rule) at the first difference, or
    // at the terminators if the strings are equal.
    return (unsigned char)*a - (unsigned char)*b;
}

int main(void) {
    printf("=== A string is chars + a '\\0' terminator ===\n");
    char hello[] = "hi";  // 3 bytes: 'h','i','\\0' — NOT 2
    printf("  \"hi\" occupies sizeof = %zu bytes (2 chars + 1 NUL)\n", sizeof hello);
    printf("  bytes (char=value): ");
    for (size_t i = 0; i < sizeof hello; i++) {
        if (hello[i] == '\0') printf("\\0=%d ", hello[i]);   // the terminator
        else                  printf("%c=%d ", hello[i], hello[i]);
    }
    printf("\n  (the trailing byte is value 0 — that's the terminator)\n");

    printf("\n=== my_strlen vs the off-by-one ===\n");
    const char *msg = "pointers";
    printf("  my_strlen(\"%s\") = %zu  (chars before '\\0')\n", msg, my_strlen(msg));
    printf("  bytes needed to STORE it = %zu  (length + 1 for the '\\0')\n",
           my_strlen(msg) + 1);

    printf("\n=== my_strcpy into a stack buffer, sized safely ===\n");
    const char *src = "hello, C";
    char buf[32];  // fixed stack buffer; plenty of room here
    // Real code guards against overflow: only copy if it fits, terminator included.
    if (my_strlen(src) + 1 <= sizeof buf) {
        my_strcpy(buf, src);
        printf("  copied \"%s\" -> buf, which now reads \"%s\"\n", src, buf);
    } else {
        printf("  refused to copy: \"%s\" would overflow buf[%zu]\n", src, sizeof buf);
    }

    printf("\n=== my_strcmp ===\n");
    printf("  my_strcmp(\"abc\", \"abc\") = %d  (equal)\n", my_strcmp("abc", "abc"));
    printf("  my_strcmp(\"abc\", \"abd\") = %d  (negative: 'c' < 'd')\n",
           my_strcmp("abc", "abd"));
    printf("  my_strcmp(\"abz\", \"abc\") = %d  (positive: 'z' > 'c')\n",
           my_strcmp("abz", "abc"));
    printf("  my_strcmp(\"ab\",  \"abc\") = %d  (negative: shorter sorts first)\n",
           my_strcmp("ab", "abc"));

    return 0;
}
