/* Exercise 47.2 — Count the words in a string  (make ex2)
 *
 * Implement count_words: return how many whitespace-separated words are in `s`.
 * Hint: scan character by character. Count each transition from "in a space" to
 * "in a word" — that's the start of a new word. isspace() (from <ctype.h>) tells
 * you if a char is whitespace. Check your answer with `make sol2`.
 */
#include <stdio.h>
#include <ctype.h>

int count_words(const char *s) {
    /* TODO: return the number of words in s */
    (void)s;      /* remove this line once you use s */
    return 0;
}

int main(void) {
    const char *text = "the quick brown fox jumps";
    printf("=== word count ===\n");
    printf("  text: \"%s\"\n", text);
    printf("  words = %d\n", count_words(text));
    return 0;
}
