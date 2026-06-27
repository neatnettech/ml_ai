// Module 40 — Demo 3: The tree-walking evaluator (AST -> result)
//
// Stage three RUNS the program by WALKING the AST: to compute a binop you
// recursively compute its two children, then combine them. This is exactly how
// the "tree-walking interpreter" in Crafting Interpreters works, condensed.
//
// We also grow the language from "expressions" to a real little program:
//   - variables   x = expr        (store a value in an environment)
//   - print       print expr      (evaluate and print)
// A program is a sequence of newline-separated statements sharing one
// environment, so later lines can read variables earlier lines set.
//
// Build & run:  make run3   — read alongside README.md §3.
//
// NOTE: this file contains a tree-walking EVALUATOR; the word "eval" appears in
// function names by long-standing tradition (it is the standard term for
// "compute the value of an AST node"), not because anything calls a shell or a
// dynamic-code eval() — there is none.

#include "ast.h"

// ---------------------------------------------------------------------------
// Environment: the symbol table mapping variable names -> integer values.
// A flat array is plenty for a demo; a real interpreter uses a hash map and
// nested scopes.
// ---------------------------------------------------------------------------
typedef struct {
    char name[64];
    long value;
} Var;

typedef struct {
    Var  vars[64];
    int  count;
} Env;

// Look up a variable's value. Undefined variables are an error here (a stricter
// choice than defaulting to 0 — it catches typos).
static long env_get(Env *env, const char *name) {
    for (int i = 0; i < env->count; i++)
        if (strcmp(env->vars[i].name, name) == 0)
            return env->vars[i].value;
    fprintf(stderr, "runtime error: undefined variable '%s'\n", name);
    exit(1);
}

// Set (or update) a variable.
static void env_set(Env *env, const char *name, long value) {
    for (int i = 0; i < env->count; i++) {
        if (strcmp(env->vars[i].name, name) == 0) {
            env->vars[i].value = value;
            return;
        }
    }
    if (env->count >= (int)(sizeof env->vars / sizeof env->vars[0])) {
        fprintf(stderr, "runtime error: too many variables\n");
        exit(1);
    }
    snprintf(env->vars[env->count].name, sizeof env->vars[0].name, "%s", name);
    env->vars[env->count].value = value;
    env->count++;
}

// ---------------------------------------------------------------------------
// The evaluator: compute the value of an AST node, recursively.
// THIS is the tree walk — note how N_BINOP evaluates both children first.
// ---------------------------------------------------------------------------
static long eval_node(const Node *n, Env *env) {
    switch (n->kind) {
        case N_NUMBER:
            return n->num;                       // a literal evaluates to itself
        case N_VAR:
            return env_get(env, n->name);        // a variable -> its stored value
        case N_BINOP: {
            long l = eval_node(n->left,  env);   // evaluate left subtree
            long r = eval_node(n->right, env);   // evaluate right subtree
            switch (n->op) {                     // then apply the operator
                case '+': return l + r;
                case '-': return l - r;
                case '*': return l * r;
                case '/':
                    if (r == 0) {
                        fprintf(stderr, "runtime error: division by zero\n");
                        exit(1);
                    }
                    return l / r;
            }
            fprintf(stderr, "runtime error: unknown operator '%c'\n", n->op);
            exit(1);
        }
    }
    return 0;  // unreachable
}

// ---------------------------------------------------------------------------
// Statement layer: run one line. A statement is one of:
//   IDENT '=' expr   -> assignment
//   'print' expr     -> print the value
//   expr             -> evaluate, value discarded (echoed here for visibility)
// We peek at the first one or two tokens to decide which it is, then hand the
// rest to the shared expression parser/evaluator.
// ---------------------------------------------------------------------------
static void run_line(const char *line, Env *env) {
    // Skip blank lines silently.
    Lexer probe;
    lex_init(&probe, line);
    Token first = lex_next(&probe);
    if (first.type == T_EOF) return;

    printf("  %-16s | ", line);

    // `print expr` — keyword `print` is just an IDENT we recognise here.
    if (first.type == T_IDENT && strcmp(first.text, "print") == 0) {
        // probe.pos points just past "print"; parse the rest as an expression.
        Node *root = parse_expression(line + probe.pos);
        long v = eval_node(root, env);
        printf("print -> %ld\n", v);
        ast_free(root);
        return;
    }

    // `IDENT = expr` — assignment. Re-lex to confirm the second token is '='.
    if (first.type == T_IDENT) {
        Lexer look;
        lex_init(&look, line);
        lex_next(&look);                 // skip IDENT
        Token second = lex_next(&look);
        if (second.type == T_ASSIGN) {
            Node *root = parse_expression(line + look.pos);  // parse RHS
            long v = eval_node(root, env);
            env_set(env, first.text, v);
            printf("%s = %ld\n", first.text, v);
            ast_free(root);
            return;
        }
    }

    // Otherwise treat the whole line as a bare expression.
    Node *root = parse_expression(line);
    long v = eval_node(root, env);
    printf("expr -> %ld\n", v);
    ast_free(root);
}

// Run a multi-line program (statements separated by '\n') in a fresh env.
static void run_program(const char *title, const char *program) {
    printf("=== %s ===\n", title);

    Env env;
    env.count = 0;

    // Walk the program line by line.
    const char *p = program;
    char line[256];
    while (*p) {
        size_t n = 0;
        while (*p && *p != '\n' && n < sizeof line - 1) line[n++] = *p++;
        line[n] = '\0';
        if (*p == '\n') p++;             // consume the newline
        run_line(line, &env);
    }
    putchar('\n');
}

int main(void) {
    // Pure arithmetic — proves precedence end to end: 2 + 3 * 4 == 14.
    run_program("arithmetic & precedence",
        "2 + 3 * 4\n"
        "(2 + 3) * 4\n"
        "100 - 4 * 5 - 2\n"
        "8 / 4 / 2\n");

    // Variables flowing between statements, then a computed print.
    run_program("variables & print",
        "x = 6\n"
        "y = 7\n"
        "print x * y\n"
        "x = x + 1\n"
        "print x\n");

    // A tiny "program": area of a circle-ish thing using integer math.
    run_program("a small program",
        "r = 5\n"
        "area = 3 * r * r\n"
        "print area\n");

    return 0;
}
