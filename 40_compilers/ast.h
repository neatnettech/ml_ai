// Module 40 — Shared front end: lexer + AST for a tiny language.
//
// This header is the SHARED CORE that every demo (01..04) and the solutions
// include. It defines three things, in the order a compiler uses them:
//
//   1. Tokens + a hand-written lexer  (text  -> stream of tokens)
//   2. The AST node types + a parser  (tokens -> a tree, recursive descent)
//   3. A few helpers (pretty-print, free) used across demos.
//
// WHY a header full of `static` functions instead of a .c + .h pair?
//   The Makefile mirrors Module 28: one source file -> one binary, no linking
//   of multiple .o's. Marking everything `static inline` means each demo gets
//   its own private copy with ZERO "duplicate symbol" link errors, and the
//   compiler discards anything a given demo doesn't call (so no -Wunused noise
//   leaks across files). For a real project you'd split this into lexer.c /
//   parser.c / ast.c — see the README's "Further reading".
//
// The language (intentionally tiny but real):
//   expr   := term (('+' | '-') term)*
//   term   := factor (('*' | '/') factor)*
//   factor := NUMBER | IDENT | '(' expr ')'
//   stmt   := IDENT '=' expr            (assignment)
//           | 'print' expr              (print statement)
//           | expr                      (bare expression; value is discarded)
// Precedence falls straight out of the grammar: '*' and '/' bind tighter than
// '+' and '-' because they live one level DEEPER in the call chain.

#ifndef AST_H
#define AST_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// ---------------------------------------------------------------------------
// 1. TOKENS
// ---------------------------------------------------------------------------
// A token is the smallest meaningful chunk of source text: one number, one
// identifier, one operator, one paren. The lexer's whole job is to turn a flat
// string into an array of these so the parser never has to look at raw chars.

typedef enum {
    T_NUMBER,   // an integer literal, e.g. 42      -> value in .num
    T_IDENT,    // an identifier,     e.g. x, print -> text  in .text
    T_PLUS,     // +
    T_MINUS,    // -
    T_STAR,     // *
    T_SLASH,    // /
    T_LPAREN,   // (
    T_RPAREN,   // )
    T_ASSIGN,   // =
    T_EOF       // end of input — a sentinel so the parser knows when to stop
} TokType;

typedef struct {
    TokType type;
    long    num;        // valid when type == T_NUMBER
    char    text[64];   // valid when type == T_IDENT (NUL-terminated)
} Token;

// Human-readable name for a token type — used by the lexer demo to print the
// token stream.
static inline const char *tok_name(TokType t) {
    switch (t) {
        case T_NUMBER: return "NUMBER";
        case T_IDENT:  return "IDENT";
        case T_PLUS:   return "PLUS";
        case T_MINUS:  return "MINUS";
        case T_STAR:   return "STAR";
        case T_SLASH:  return "SLASH";
        case T_LPAREN: return "LPAREN";
        case T_RPAREN: return "RPAREN";
        case T_ASSIGN: return "ASSIGN";
        case T_EOF:    return "EOF";
    }
    return "?";
}

// ---------------------------------------------------------------------------
// 1b. THE LEXER (a.k.a. scanner / tokenizer)
// ---------------------------------------------------------------------------
// A Lexer is just a cursor over the source string plus a one-token lookbuffer.
// We scan on demand: each call to lex_next() skips whitespace, looks at the
// next character, and decides which token it begins.

typedef struct {
    const char *src;   // the source text (not owned)
    size_t      pos;   // index of the next char to read
} Lexer;

static inline void lex_init(Lexer *lx, const char *src) {
    lx->src = src;
    lx->pos = 0;
}

// Produce the next token. This is the heart of the lexer — a small dispatch on
// the leading character. Real lexers add string/char literals, comments, and
// multi-char operators here, but the shape stays the same.
static inline Token lex_next(Lexer *lx) {
    Token tk;
    memset(&tk, 0, sizeof tk);

    // Skip whitespace: it separates tokens but is not itself a token.
    while (lx->src[lx->pos] != '\0' && isspace((unsigned char)lx->src[lx->pos]))
        lx->pos++;

    char c = lx->src[lx->pos];

    if (c == '\0') {            // end of input
        tk.type = T_EOF;
        return tk;
    }

    // A run of digits is one NUMBER token. We accumulate the integer value as
    // we go — the lexer, not the parser, converts text "42" into the long 42.
    if (isdigit((unsigned char)c)) {
        long value = 0;
        while (isdigit((unsigned char)lx->src[lx->pos])) {
            value = value * 10 + (lx->src[lx->pos] - '0');
            lx->pos++;
        }
        tk.type = T_NUMBER;
        tk.num  = value;
        return tk;
    }

    // A letter (or '_') starts an IDENT: a variable name or a keyword like
    // `print`. We copy the run of identifier chars into tk.text.
    if (isalpha((unsigned char)c) || c == '_') {
        size_t n = 0;
        while ((isalnum((unsigned char)lx->src[lx->pos]) || lx->src[lx->pos] == '_')
               && n < sizeof tk.text - 1) {
            tk.text[n++] = lx->src[lx->pos++];
        }
        tk.text[n] = '\0';
        tk.type = T_IDENT;
        return tk;
    }

    // Otherwise it's a single-character operator/punctuation token.
    lx->pos++;  // consume the character
    switch (c) {
        case '+': tk.type = T_PLUS;   return tk;
        case '-': tk.type = T_MINUS;  return tk;
        case '*': tk.type = T_STAR;   return tk;
        case '/': tk.type = T_SLASH;  return tk;
        case '(': tk.type = T_LPAREN; return tk;
        case ')': tk.type = T_RPAREN; return tk;
        case '=': tk.type = T_ASSIGN; return tk;
        default:
            fprintf(stderr, "lex error: unexpected character '%c'\n", c);
            exit(1);
    }
}

// ---------------------------------------------------------------------------
// 2. THE AST (abstract syntax tree)
// ---------------------------------------------------------------------------
// The parser turns the token stream into a TREE. Each node is one of:
//   - a number literal           (leaf)
//   - a variable reference       (leaf)
//   - a binary operation         (two children: left op right)
// `2 + 3 * 4` becomes  (+ 2 (* 3 4))  — the tree shape ENCODES precedence, so
// the evaluator never has to think about it again.

typedef enum {
    N_NUMBER,   // .num
    N_VAR,      // .name
    N_BINOP     // .op, .left, .right
} NodeKind;

typedef struct Node {
    NodeKind kind;
    // N_NUMBER
    long num;
    // N_VAR
    char name[64];
    // N_BINOP
    char op;            // '+', '-', '*', '/'  (and operators you add in exercises)
    struct Node *left;
    struct Node *right;
} Node;

// Node constructors. malloc each node; the tree is freed with ast_free().
static inline Node *node_number(long v) {
    Node *n = (Node *)calloc(1, sizeof *n);
    n->kind = N_NUMBER;
    n->num  = v;
    return n;
}
static inline Node *node_var(const char *name) {
    Node *n = (Node *)calloc(1, sizeof *n);
    n->kind = N_VAR;
    snprintf(n->name, sizeof n->name, "%s", name);
    return n;
}
static inline Node *node_binop(char op, Node *l, Node *r) {
    Node *n = (Node *)calloc(1, sizeof *n);
    n->kind  = N_BINOP;
    n->op    = op;
    n->left  = l;
    n->right = r;
    return n;
}

// Recursively free a tree. Post-order: free children before the parent so we
// never dereference freed memory. Call this on every root you build.
static inline void ast_free(Node *n) {
    if (!n) return;
    if (n->kind == N_BINOP) {
        ast_free(n->left);
        ast_free(n->right);
    }
    free(n);
}

// ---------------------------------------------------------------------------
// 2b. THE PARSER (recursive descent)
// ---------------------------------------------------------------------------
// One C function per grammar rule. The Parser holds the current token; each
// function consumes the tokens its rule covers and returns a subtree. Because
// term() is called from expr() and factor() from term(), the *call stack*
// mirrors the grammar — that's what "recursive descent" means.

typedef struct {
    Lexer lx;
    Token cur;   // the current (lookahead) token
} Parser;

static inline void parser_init(Parser *p, const char *src) {
    lex_init(&p->lx, src);
    p->cur = lex_next(&p->lx);   // prime the lookahead
}

// Advance to the next token, returning the one we just left behind.
static inline Token parser_advance(Parser *p) {
    Token prev = p->cur;
    p->cur = lex_next(&p->lx);
    return prev;
}

// Require the current token to be `type`; consume it or die. Used to enforce
// grammar like the ')' that must close a '('.
static inline void parser_expect(Parser *p, TokType type) {
    if (p->cur.type != type) {
        fprintf(stderr, "parse error: expected %s but got %s\n",
                tok_name(type), tok_name(p->cur.type));
        exit(1);
    }
    parser_advance(p);
}

// Forward declaration: factor() needs expr() for the '(' expr ')' case.
static inline Node *parse_expr(Parser *p);

// factor := NUMBER | IDENT | '(' expr ')'
// The atoms of the grammar: a literal, a variable, or a parenthesised group.
static inline Node *parse_factor(Parser *p) {
    if (p->cur.type == T_NUMBER) {
        long v = p->cur.num;
        parser_advance(p);
        return node_number(v);
    }
    if (p->cur.type == T_IDENT) {
        char name[64];
        snprintf(name, sizeof name, "%s", p->cur.text);
        parser_advance(p);
        return node_var(name);
    }
    if (p->cur.type == T_LPAREN) {
        parser_advance(p);                 // eat '('
        Node *inner = parse_expr(p);       // parse whatever is inside
        parser_expect(p, T_RPAREN);        // must be closed by ')'
        return inner;                      // parens just group; no node needed
    }
    fprintf(stderr, "parse error: unexpected %s in factor\n", tok_name(p->cur.type));
    exit(1);
}

// term := factor (('*' | '/') factor)*
// Left-associative: we fold left-to-right into a left-leaning tree, so
// 8 / 4 / 2 parses as ((8 / 4) / 2) = 1, not 8 / (4 / 2) = 4.
static inline Node *parse_term(Parser *p) {
    Node *left = parse_factor(p);
    while (p->cur.type == T_STAR || p->cur.type == T_SLASH) {
        char op = (p->cur.type == T_STAR) ? '*' : '/';
        parser_advance(p);
        Node *right = parse_factor(p);
        left = node_binop(op, left, right);
    }
    return left;
}

// expr := term (('+' | '-') term)*
// The lowest-precedence level. Because '+'/'-' live here and '*'/'/' live one
// level down in term(), multiplication always binds tighter — no precedence
// table required.
static inline Node *parse_expr(Parser *p) {
    Node *left = parse_term(p);
    while (p->cur.type == T_PLUS || p->cur.type == T_MINUS) {
        char op = (p->cur.type == T_PLUS) ? '+' : '-';
        parser_advance(p);
        Node *right = parse_term(p);
        left = node_binop(op, left, right);
    }
    return left;
}

// Parse a whole expression string and ensure nothing is left over.
static inline Node *parse_expression(const char *src) {
    Parser p;
    parser_init(&p, src);
    Node *root = parse_expr(&p);
    parser_expect(&p, T_EOF);   // reject trailing garbage like "1 2"
    return root;
}

// ---------------------------------------------------------------------------
// 2c. PRETTY-PRINT THE AST
// ---------------------------------------------------------------------------
// Fully parenthesised, so the tree's structure (and thus precedence) is
// unambiguous on the page: 2 + 3 * 4 -> (2 + (3 * 4)).
static inline void ast_print(const Node *n) {
    switch (n->kind) {
        case N_NUMBER:
            printf("%ld", n->num);
            break;
        case N_VAR:
            printf("%s", n->name);
            break;
        case N_BINOP:
            putchar('(');
            ast_print(n->left);
            printf(" %c ", n->op);
            ast_print(n->right);
            putchar(')');
            break;
    }
}

#endif // AST_H
