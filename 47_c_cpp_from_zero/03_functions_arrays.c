/* Module 47 — Demo 3: reusable code, lists, and text.
 *
 * A function packages logic behind a name so you call it instead of repeating
 * it. Arguments are passed BY VALUE in C — the function gets a copy, so writing
 * to a plain parameter never touches the caller's variable. (Demo 4 shows how
 * pointers get around that.) Arrays are fixed-size runs of one type; a C string
 * is just a char array ending in a '\0' terminator byte.
 */
#include <stdio.h>
#include <string.h>

/* return values */
int square(int n) { return n * n; }

int sum(const int *a, int len) {
    int total = 0;
    for (int i = 0; i < len; i++) total += a[i];
    return total;
}

int max_of(const int *a, int len) {
    int best = a[0];
    for (int i = 1; i < len; i++)
        if (a[i] > best) best = a[i];
    return best;
}

/* reverse a C string in place */
void reverse_string(char *s) {
    int len = (int)strlen(s);
    for (int i = 0, j = len - 1; i < j; i++, j--) {
        char tmp = s[i];
        s[i] = s[j];
        s[j] = tmp;
    }
}

int main(void) {
    printf("=== functions ===\n");
    printf("  square(6) = %d\n", square(6));

    int nums[] = {1, 2, 3, 4, 5};
    int len = (int)(sizeof(nums) / sizeof(nums[0]));
    printf("  sum([1,2,3,4,5]) = %d\n", sum(nums, len));

    printf("=== arrays ===\n");
    int vals[] = {4, 9, 2, 7, 1};
    printf("  max of {4, 9, 2, 7, 1} = %d\n",
           max_of(vals, (int)(sizeof(vals) / sizeof(vals[0]))));

    printf("=== C strings (char arrays) ===\n");
    char word[] = "hello";
    size_t wlen = strlen(word);
    reverse_string(word);
    printf("  \"hello\" reversed is \"%s\"  (length %zu)\n", word, wlen);
    return 0;
}
