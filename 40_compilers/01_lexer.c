// Module 40 — Demo 1: The lexer (text -> token stream)
//
// A compiler's first stage is LEXING (a.k.a. scanning or tokenizing): turning a
// flat run of characters into a list of meaningful tokens. "(2 + 3) * 4" is
// just bytes until the lexer chops it into LPAREN NUMBER(2) PLUS NUMBER(3)
// RPAREN STAR NUMBER(4) EOF — and only then can a parser make sense of it.
//
// The lexer itself lives in ast.h (lex_init / lex_next). This demo just drives
// it across a few source strings and prints what comes out. Build & run:
//   make run1
//
// Read alongside README.md §1.

#include "ast.h"

// Tokenize one source string completely and print every token in order.
static void dump_tokens(const char *src) {
    printf("source: \"%s\"\n", src);

    Lexer lx;
    lex_init(&lx, src);

    // Pull tokens until EOF. lex_next() never returns past EOF, so this loop is
    // guaranteed to terminate as long as the input is valid.
    for (;;) {
        Token tk = lex_next(&lx);

        // Print the token's kind, plus its payload for the two kinds that carry
        // one (numbers carry a value, identifiers carry their text).
        printf("  %-7s", tok_name(tk.type));
        if (tk.type == T_NUMBER) printf(" %ld", tk.num);
        else if (tk.type == T_IDENT) printf(" \"%s\"", tk.text);
        putchar('\n');

        if (tk.type == T_EOF) break;
    }
    putchar('\n');
}

int main(void) {
    // A pure-arithmetic expression: note how parens and operators each become
    // their own single-character token.
    dump_tokens("(2 + 3) * 4");

    // Precedence is NOT the lexer's job — it emits a flat stream. The parser
    // (demo 2) is what gives '*' priority over '+'.
    dump_tokens("2 + 3 * 4");

    // Identifiers and keywords look the same to the lexer: `print` and `x` are
    // both IDENT tokens. The parser decides `print` is special (demo 3).
    dump_tokens("x = 10");
    dump_tokens("print x * x");

    return 0;
}
