// Exercise 40.1 — Add the modulo operator `%` end to end
//
// Right now this mini-interpreter handles + - * / with correct precedence. Your
// job: thread a NEW operator, `%` (modulo / remainder), through ALL THREE
// stages — lexer, parser, evaluator — so that a program string using `%`
// evaluates correctly. `%` has the same precedence/associativity as `*` and `/`.
//
// There are THREE // TODO spots below. When done, `make ex1` should match the
// expected output in README.md §6 (e.g. 17 % 5 == 2, and 2 + 17 % 5 == 4 to
// prove precedence). Reference answer in ../solutions/ex1_modulo.c.
//
// This file is intentionally self-contained (it does NOT include ast.h) so you
// can edit the lexer and parser directly.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// ---- tokens ---------------------------------------------------------------
typedef enum {
    T_NUMBER, T_PLUS, T_MINUS, T_STAR, T_SLASH,
    // TODO 1 of 3: add a token type for '%', e.g. T_PERCENT, to this enum.
    T_LPAREN, T_RPAREN, T_EOF
} TokType;

typedef struct { TokType type; long num; } Token;

typedef struct { const char *src; size_t pos; } Lexer;
static void lex_init(Lexer *lx, const char *s) { lx->src = s; lx->pos = 0; }

static Token lex_next(Lexer *lx) {
    Token tk; tk.type = T_EOF; tk.num = 0;
    while (lx->src[lx->pos] && isspace((unsigned char)lx->src[lx->pos])) lx->pos++;
    char c = lx->src[lx->pos];
    if (!c) return tk;
    if (isdigit((unsigned char)c)) {
        long v = 0;
        while (isdigit((unsigned char)lx->src[lx->pos])) v = v * 10 + (lx->src[lx->pos++] - '0');
        tk.type = T_NUMBER; tk.num = v; return tk;
    }
    lx->pos++;
    switch (c) {
        case '+': tk.type = T_PLUS;   return tk;
        case '-': tk.type = T_MINUS;  return tk;
        case '*': tk.type = T_STAR;   return tk;
        case '/': tk.type = T_SLASH;  return tk;
        // TODO 2 of 3: lex '%' into your new token type (mirror the '*' case).
        case '(': tk.type = T_LPAREN; return tk;
        case ')': tk.type = T_RPAREN; return tk;
        default: fprintf(stderr, "lex error: '%c'\n", c); exit(1);
    }
}

// ---- AST ------------------------------------------------------------------
typedef enum { N_NUMBER, N_BINOP } NodeKind;
typedef struct Node { NodeKind kind; long num; char op; struct Node *l, *r; } Node;

static Node *num(long v)               { Node *n = calloc(1, sizeof *n); n->kind = N_NUMBER; n->num = v; return n; }
static Node *bin(char op, Node *l, Node *r) { Node *n = calloc(1, sizeof *n); n->kind = N_BINOP; n->op = op; n->l = l; n->r = r; return n; }
static void freeast(Node *n) { if (!n) return; if (n->kind == N_BINOP) { freeast(n->l); freeast(n->r); } free(n); }

// ---- parser ---------------------------------------------------------------
typedef struct { Lexer lx; Token cur; } Parser;
static void p_init(Parser *p, const char *s) { lex_init(&p->lx, s); p->cur = lex_next(&p->lx); }
static void p_adv(Parser *p) { p->cur = lex_next(&p->lx); }

static Node *p_expr(Parser *p);
static Node *p_factor(Parser *p) {
    if (p->cur.type == T_NUMBER) { long v = p->cur.num; p_adv(p); return num(v); }
    if (p->cur.type == T_LPAREN) { p_adv(p); Node *e = p_expr(p);
        if (p->cur.type != T_RPAREN) { fprintf(stderr, "parse error: expected )\n"); exit(1); }
        p_adv(p); return e; }
    fprintf(stderr, "parse error in factor\n"); exit(1);
}
static Node *p_term(Parser *p) {
    Node *l = p_factor(p);
    // TODO 3 of 3: also accept your '%' token here (alongside '*' and '/') so
    // it parses at the SAME precedence level as multiply/divide. Map it to the
    // AST op '%'.
    while (p->cur.type == T_STAR || p->cur.type == T_SLASH) {
        char op = (p->cur.type == T_STAR) ? '*' : '/';
        p_adv(p); l = bin(op, l, p_factor(p));
    }
    return l;
}
static Node *p_expr(Parser *p) {
    Node *l = p_term(p);
    while (p->cur.type == T_PLUS || p->cur.type == T_MINUS) {
        char op = (p->cur.type == T_PLUS) ? '+' : '-';
        p_adv(p); l = bin(op, l, p_term(p));
    }
    return l;
}

// ---- evaluator ------------------------------------------------------------
static long compute(const Node *n) {
    if (n->kind == N_NUMBER) return n->num;
    long a = compute(n->l), b = compute(n->r);
    switch (n->op) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/': return a / b;
        // The evaluator already knows '%': once your AST produces an op '%',
        // this line computes the remainder. (No TODO here — the work is in the
        // lexer and parser above.)
        case '%': return a % b;
    }
    fprintf(stderr, "eval error: op '%c'\n", n->op); exit(1);
}

static void run(const char *src) {
    Parser p; p_init(&p, src);
    Node *root = p_expr(&p);
    printf("  %-14s = %ld\n", src, compute(root));
    freeast(root);
}

int main(void) {
    run("17 % 5");        // expect 2
    run("2 + 17 % 5");    // expect 4  (% binds tighter than +)
    run("(2 + 17) % 5");  // expect 4
    run("20 % 6 * 2");    // expect 4  ((20 % 6) * 2)
    return 0;
}
