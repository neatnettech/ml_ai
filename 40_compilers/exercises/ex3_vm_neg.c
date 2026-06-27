// Exercise 40.3 — Add a NEG opcode to the stack VM and emit it
//
// This is a self-contained pipeline (parse -> compile -> run on a stack VM) that
// already supports unary minus IN THE PARSER (it builds an N_NEG node). But the
// COMPILER doesn't yet know how to turn N_NEG into bytecode, and the VM doesn't
// yet know how to execute it. Your job: add the OP_NEG instruction end to end.
//
// NEG is a UNARY stack op: pop one value, push its negation.
//   PUSH 5    stack: [5]
//   NEG       stack: [-5]
//
// There are THREE // TODO spots:
//   1. add OP_NEG to the OpCode enum
//   2. make op_name() print "NEG"
//   3. emit OP_NEG when compiling an N_NEG node
//   ...and the VM's execute loop already has a NEG case waiting? No — you add
//      that too (TODO 4). Four small edits, all marked.
//
// When done, `make ex3` should match README.md §6: the disassembly shows a NEG
// instruction and "-5", "3 * -2 == -6" run correctly. Reference:
// ../solutions/ex3_vm_neg.c.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// ---- tokens + lexer -------------------------------------------------------
typedef enum { T_NUMBER, T_PLUS, T_MINUS, T_STAR, T_SLASH, T_LPAREN, T_RPAREN, T_EOF } TokType;
typedef struct { TokType type; long num; } Token;
typedef struct { const char *src; size_t pos; } Lexer;
static void lex_init(Lexer *lx, const char *s) { lx->src = s; lx->pos = 0; }
static Token lex_next(Lexer *lx) {
    Token tk; tk.type = T_EOF; tk.num = 0;
    while (lx->src[lx->pos] && isspace((unsigned char)lx->src[lx->pos])) lx->pos++;
    char c = lx->src[lx->pos];
    if (!c) return tk;
    if (isdigit((unsigned char)c)) { long v = 0;
        while (isdigit((unsigned char)lx->src[lx->pos])) v = v * 10 + (lx->src[lx->pos++] - '0');
        tk.type = T_NUMBER; tk.num = v; return tk; }
    lx->pos++;
    switch (c) {
        case '+': tk.type = T_PLUS;   return tk;
        case '-': tk.type = T_MINUS;  return tk;
        case '*': tk.type = T_STAR;   return tk;
        case '/': tk.type = T_SLASH;  return tk;
        case '(': tk.type = T_LPAREN; return tk;
        case ')': tk.type = T_RPAREN; return tk;
        default: fprintf(stderr, "lex error: '%c'\n", c); exit(1);
    }
}

// ---- AST + parser (unary minus already supported) -------------------------
typedef enum { N_NUMBER, N_BINOP, N_NEG } NodeKind;
typedef struct Node { NodeKind kind; long num; char op; struct Node *l, *r; } Node;
static Node *num(long v) { Node *n = calloc(1, sizeof *n); n->kind = N_NUMBER; n->num = v; return n; }
static Node *bin(char op, Node *l, Node *r) { Node *n = calloc(1, sizeof *n); n->kind = N_BINOP; n->op = op; n->l = l; n->r = r; return n; }
static Node *neg(Node *c) { Node *n = calloc(1, sizeof *n); n->kind = N_NEG; n->l = c; return n; }
static void freeast(Node *n) { if (!n) return;
    if (n->kind == N_BINOP) { freeast(n->l); freeast(n->r); }
    else if (n->kind == N_NEG) { freeast(n->l); } free(n); }

typedef struct { Lexer lx; Token cur; } Parser;
static void p_init(Parser *p, const char *s) { lex_init(&p->lx, s); p->cur = lex_next(&p->lx); }
static void p_adv(Parser *p) { p->cur = lex_next(&p->lx); }
static Node *p_expr(Parser *p);
static Node *p_factor(Parser *p) {
    if (p->cur.type == T_MINUS) { p_adv(p); return neg(p_factor(p)); }
    if (p->cur.type == T_NUMBER) { long v = p->cur.num; p_adv(p); return num(v); }
    if (p->cur.type == T_LPAREN) { p_adv(p); Node *e = p_expr(p);
        if (p->cur.type != T_RPAREN) { fprintf(stderr, "parse error: )\n"); exit(1); }
        p_adv(p); return e; }
    fprintf(stderr, "parse error in factor\n"); exit(1);
}
static Node *p_term(Parser *p) { Node *l = p_factor(p);
    while (p->cur.type == T_STAR || p->cur.type == T_SLASH) {
        char op = (p->cur.type == T_STAR) ? '*' : '/'; p_adv(p); l = bin(op, l, p_factor(p)); }
    return l; }
static Node *p_expr(Parser *p) { Node *l = p_term(p);
    while (p->cur.type == T_PLUS || p->cur.type == T_MINUS) {
        char op = (p->cur.type == T_PLUS) ? '+' : '-'; p_adv(p); l = bin(op, l, p_term(p)); }
    return l; }

// ---- bytecode -------------------------------------------------------------
typedef enum {
    OP_PUSH, OP_ADD, OP_SUB, OP_MUL, OP_DIV
    // TODO 1 of 4: add OP_NEG here.
} OpCode;

static const char *op_name(OpCode op) {
    switch (op) {
        case OP_PUSH: return "PUSH";
        case OP_ADD:  return "ADD";
        case OP_SUB:  return "SUB";
        case OP_MUL:  return "MUL";
        case OP_DIV:  return "DIV";
        // TODO 2 of 4: return "NEG" for OP_NEG.
    }
    return "?";
}

typedef struct { OpCode op; long arg; } Instr;
typedef struct { Instr *code; int count, cap; } Chunk;
static void chunk_init(Chunk *c) { c->code = NULL; c->count = c->cap = 0; }
static void chunk_free(Chunk *c) { free(c->code); c->code = NULL; c->count = c->cap = 0; }
static void emit(Chunk *c, OpCode op, long arg) {
    if (c->count == c->cap) { c->cap = c->cap ? c->cap * 2 : 8;
        c->code = realloc(c->code, (size_t)c->cap * sizeof *c->code); }
    c->code[c->count].op = op; c->code[c->count].arg = arg; c->count++;
}

// ---- compiler -------------------------------------------------------------
static void compile(const Node *n, Chunk *c) {
    if (n->kind == N_NUMBER) { emit(c, OP_PUSH, n->num); return; }
    if (n->kind == N_NEG) {
        compile(n->l, c);
        // TODO 3 of 4: emit OP_NEG here (it negates whatever the child left on
        // the stack). Hint: emit(c, OP_NEG, 0);
        return;
    }
    // N_BINOP
    compile(n->l, c);
    compile(n->r, c);
    switch (n->op) {
        case '+': emit(c, OP_ADD, 0); break;
        case '-': emit(c, OP_SUB, 0); break;
        case '*': emit(c, OP_MUL, 0); break;
        case '/': emit(c, OP_DIV, 0); break;
    }
}

static void disassemble(const Chunk *c) {
    for (int i = 0; i < c->count; i++) {
        printf("    %04d  %-4s", i, op_name(c->code[i].op));
        if (c->code[i].op == OP_PUSH) printf(" %ld", c->code[i].arg);
        putchar('\n');
    }
}

// ---- VM -------------------------------------------------------------------
static long vm_run(const Chunk *c) {
    long st[256]; int sp = 0;
    for (int ip = 0; ip < c->count; ip++) {
        Instr in = c->code[ip];
        switch (in.op) {
            case OP_PUSH: st[sp++] = in.arg; break;
            case OP_ADD: { long b = st[--sp], a = st[--sp]; st[sp++] = a + b; break; }
            case OP_SUB: { long b = st[--sp], a = st[--sp]; st[sp++] = a - b; break; }
            case OP_MUL: { long b = st[--sp], a = st[--sp]; st[sp++] = a * b; break; }
            case OP_DIV: { long b = st[--sp], a = st[--sp]; st[sp++] = a / b; break; }
            // TODO 4 of 4: add a case for OP_NEG: pop one value, push its
            // negation. Hint: long a = st[--sp]; st[sp++] = -a;
        }
    }
    return st[0];
}

static void run(const char *src) {
    printf("=== %s ===\n", src);
    Parser p; p_init(&p, src);
    Node *root = p_expr(&p);
    Chunk c; chunk_init(&c);
    compile(root, &c);
    disassemble(&c);
    printf("  result: %ld\n\n", vm_run(&c));
    chunk_free(&c);
    freeast(root);
}

int main(void) {
    run("-5");       // expect -5,  bytecode: PUSH 5 / NEG
    run("3 * -2");   // expect -6
    run("-(2 + 3)"); // expect -5
    return 0;
}
