// Module 40 — Demo 4: Bytecode compiler + stack VM (AST -> bytecode -> result)
//
// A tree-walking interpreter (demo 3) re-walks the tree every time. Faster
// languages COMPILE the AST once into a flat list of instructions — BYTECODE —
// then execute that on a virtual machine. This is the Nand2Tetris VM idea and
// the second half of Crafting Interpreters, condensed to four arithmetic ops.
//
// Our VM is a STACK MACHINE: every instruction works on a stack of values.
//   PUSH n   push the constant n
//   ADD      pop b, pop a, push a+b
//   SUB      pop b, pop a, push a-b
//   MUL      pop b, pop a, push a*b
//   DIV      pop b, pop a, push a/b
// To compile a binop we emit code for the left subtree, then the right, then
// the operator — a post-order walk. That ordering is exactly why a stack works:
// when ADD runs, its two operands are the top two stack slots.
//
// Build & run:  make run4   — read alongside README.md §4.

#include "ast.h"

// ---------------------------------------------------------------------------
// The instruction set.
// ---------------------------------------------------------------------------
typedef enum {
    OP_PUSH,   // has a 1-operand argument (the constant)
    OP_ADD,
    OP_SUB,
    OP_MUL,
    OP_DIV
} OpCode;

static const char *op_name(OpCode op) {
    switch (op) {
        case OP_PUSH: return "PUSH";
        case OP_ADD:  return "ADD";
        case OP_SUB:  return "SUB";
        case OP_MUL:  return "MUL";
        case OP_DIV:  return "DIV";
    }
    return "?";
}

// A compiled instruction: an opcode plus an optional operand (only PUSH uses it).
typedef struct {
    OpCode op;
    long   arg;
} Instr;

// A growable chunk of bytecode.
typedef struct {
    Instr *code;
    int    count;
    int    cap;
} Chunk;

static void chunk_init(Chunk *c) {
    c->code  = NULL;
    c->count = 0;
    c->cap   = 0;
}
static void chunk_free(Chunk *c) {
    free(c->code);
    c->code  = NULL;
    c->count = 0;
    c->cap   = 0;
}
// Append one instruction, growing the array as needed.
static void chunk_emit(Chunk *c, OpCode op, long arg) {
    if (c->count == c->cap) {
        c->cap = c->cap ? c->cap * 2 : 8;
        c->code = (Instr *)realloc(c->code, (size_t)c->cap * sizeof *c->code);
    }
    c->code[c->count].op  = op;
    c->code[c->count].arg = arg;
    c->count++;
}

// ---------------------------------------------------------------------------
// The COMPILER: recursively turn an AST into bytecode (post-order traversal).
// (No variables here — demo 4 stays focused on arithmetic. Extending the VM to
// load/store variables is a natural follow-on; exercise 3 extends the opcodes.)
// ---------------------------------------------------------------------------
static void compile(const Node *n, Chunk *c) {
    switch (n->kind) {
        case N_NUMBER:
            chunk_emit(c, OP_PUSH, n->num);   // a literal -> push it
            return;
        case N_VAR:
            fprintf(stderr, "compile error: variables not supported in the VM demo\n");
            exit(1);
        case N_BINOP:
            compile(n->left,  c);             // 1. code that leaves left  on stack
            compile(n->right, c);             // 2. code that leaves right on stack
            switch (n->op) {                  // 3. the op consumes both, pushes result
                case '+': chunk_emit(c, OP_ADD, 0); break;
                case '-': chunk_emit(c, OP_SUB, 0); break;
                case '*': chunk_emit(c, OP_MUL, 0); break;
                case '/': chunk_emit(c, OP_DIV, 0); break;
                default:
                    fprintf(stderr, "compile error: bad operator '%c'\n", n->op);
                    exit(1);
            }
            return;
    }
}

// ---------------------------------------------------------------------------
// The DISASSEMBLER: print bytecode in human-readable form (like `objdump`).
// ---------------------------------------------------------------------------
static void disassemble(const Chunk *c) {
    for (int i = 0; i < c->count; i++) {
        printf("    %04d  %-4s", i, op_name(c->code[i].op));
        if (c->code[i].op == OP_PUSH) printf(" %ld", c->code[i].arg);
        putchar('\n');
    }
}

// ---------------------------------------------------------------------------
// The VM: execute a chunk on a value stack and return the final result.
// This is a classic fetch-decode-execute loop.
// ---------------------------------------------------------------------------
static long vm_run(const Chunk *c) {
    long stack[256];
    int  sp = 0;   // stack pointer = index of the next free slot

    for (int ip = 0; ip < c->count; ip++) {   // ip = instruction pointer
        Instr in = c->code[ip];
        switch (in.op) {
            case OP_PUSH:
                stack[sp++] = in.arg;
                break;
            // Each binary op pops the top two (right was pushed last, so it's on
            // top), applies the op, and pushes the result.
            case OP_ADD: { long b = stack[--sp], a = stack[--sp]; stack[sp++] = a + b; break; }
            case OP_SUB: { long b = stack[--sp], a = stack[--sp]; stack[sp++] = a - b; break; }
            case OP_MUL: { long b = stack[--sp], a = stack[--sp]; stack[sp++] = a * b; break; }
            case OP_DIV: {
                long b = stack[--sp], a = stack[--sp];
                if (b == 0) { fprintf(stderr, "vm error: division by zero\n"); exit(1); }
                stack[sp++] = a / b;
                break;
            }
        }
    }
    // A well-formed expression leaves exactly one value on the stack: the answer.
    return stack[0];
}

// Drive the whole pipeline for one expression: parse -> compile -> show -> run.
static void run_vm(const char *src) {
    printf("=== %s ===\n", src);

    Node *ast = parse_expression(src);
    printf("  AST:        ");
    ast_print(ast);
    putchar('\n');

    Chunk chunk;
    chunk_init(&chunk);
    compile(ast, &chunk);

    printf("  bytecode:\n");
    disassemble(&chunk);

    long result = vm_run(&chunk);
    printf("  result:     %ld\n\n", result);

    chunk_free(&chunk);
    ast_free(ast);
}

int main(void) {
    // The precedence case again, now proven through the VM: 2 + 3 * 4 == 14.
    run_vm("2 + 3 * 4");

    // Parens change the bytecode order and the answer: (2 + 3) * 4 == 20.
    run_vm("(2 + 3) * 4");

    // Left-associative division compiles to ((8 / 4) / 2) == 1.
    run_vm("8 / 4 / 2");

    return 0;
}
