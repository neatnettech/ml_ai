/* Exercise 47.2 — Count the words in a string  (reference solution, make sol2) */
#include <stdio.h>
#include <ctype.h>

int count_words(const char *s) {
    int count = 0;
    int in_word = 0;
    for (; *s != '\0'; s++) {
        if (isspace((unsigned char)*s)) {
            in_word = 0;
        } else if (!in_word) {
            in_word = 1;      /* transition space -> word starts a new word */
            count++;
        }
    }
    return count;
}

int main(void) {
    const char *text = "the quick brown fox jumps";
    printf("=== word count ===\n");
    printf("  text: \"%s\"\n", text);
    printf("  words = %d\n", count_words(text));
    return 0;
}
