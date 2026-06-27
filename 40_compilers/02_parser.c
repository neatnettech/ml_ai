// Module 40 — Demo 2: The parser (tokens -> AST)
//
// The parser is stage two: it consumes the lexer's token stream and builds an
// ABSTRACT SYNTAX TREE that captures how the operators nest. The crucial trick
// is PRECEDENCE and ASSOCIATIVITY — `2 + 3 * 4` must become (2 + (3 * 4)) = 14,
// not ((2 + 3) * 4) = 20. Our recursive-descent parser (in ast.h) gets this for
// free by layering its grammar: '+'/'-' at the outer level, '*'/'/' deeper.
//
// This demo parses several expressions and pretty-prints each AST fully
// parenthesised, so you can SEE the structure the parser chose. Build & run:
//   make run2
//
// Read alongside README.md §2.

#include "ast.h"

// Parse one expression and print "src  =>  (fully parenthesised AST)".
static void show_ast(const char *src) {
    Node *root = parse_expression(src);
    printf("  %-14s =>  ", src);
    ast_print(root);
    putchar('\n');
    ast_free(root);   // every tree we build, we free — no leaks (try valgrind)
}

int main(void) {
    printf("Each expression, then the AST the parser built (parenthesised):\n\n");

    // The headline precedence case: '*' binds tighter than '+'.
    show_ast("2 + 3 * 4");      // => (2 + (3 * 4))   value would be 14

    // Parens override precedence, forcing the addition first.
    show_ast("(2 + 3) * 4");    // => ((2 + 3) * 4)   value would be 20

    // Left-associativity of subtraction: ((10 - 3) - 2), not (10 - (3 - 2)).
    show_ast("10 - 3 - 2");     // => ((10 - 3) - 2)

    // Left-associativity of division too: ((8 / 4) / 2) = 1.
    show_ast("8 / 4 / 2");      // => ((8 / 4) / 2)

    // Mixed precedence across all four operators.
    show_ast("1 + 2 * 3 - 4");  // => ((1 + (2 * 3)) - 4)

    // Variables are leaves just like numbers.
    show_ast("x * x + 1");      // => ((x * x) + 1)

    return 0;
}
