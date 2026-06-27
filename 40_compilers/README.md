# Module 40 — Compilers & Language Engineering

**Purpose:** A compiler or interpreter is the bridge between the text you type and
the machine that runs it — and it is one of the most demystifying things you can
build, because *every* stage is small and inspectable. In this module you build a
real (if tiny) language **end to end**: a hand-written lexer turns source text into
tokens, a recursive-descent parser turns tokens into an abstract syntax tree, a
tree-walking evaluator runs that tree, and a bytecode compiler + stack VM shows the
*other* way to execute it. By the end you'll know exactly what happens between
`2 + 3 * 4` and the answer `14` — including why it's `14` and not `20`.

**Prerequisites:** Module 30 (C pointers & structs — the AST is a tree of malloc'd
nodes) and Module 38 (recursion & data structures — the parser and the tree walk
are both recursion over a tree). No prior compiler experience assumed; we build
every stage from scratch.

**What you'll learn:**
- **Lexing:** turning a flat string into a stream of typed tokens (a hand-written
  scanner — no regex, no generator)
- **Parsing:** **recursive descent**, and how layering the grammar gives you correct
  operator **precedence** and **associativity** for free (`2 + 3 * 4 == 14`)
- **ASTs:** representing a program as a tree, building it, pretty-printing it, and
  freeing it
- **Tree-walking evaluation:** running the AST directly; adding **variables** and a
  **`print`** statement to grow expressions into a real little language
- **Bytecode + a stack VM:** compiling the AST to flat instructions
  (`PUSH/ADD/SUB/MUL/DIV/NEG`) and executing them — the Nand2Tetris VM idea and the
  second half of *Crafting Interpreters*, condensed

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 40 runs **natively on Apple Silicon** — no container needed. You only need
`clang` + `make` (Xcode Command Line Tools):

```bash
make            # build all four demos + exercises + solutions
make run        # build + run all four demos in order
```

The shared front end (lexer + AST + parser) lives in [`ast.h`](ast.h) as `static
inline` functions so each demo is one self-contained binary; the exercises are
fully standalone so you can edit the lexer/parser directly. In a production
compiler you'd split these into `lexer.c` / `parser.c` / `ast.c` — see *Further
reading*.

---

## 1. The lexer: text → tokens

The first stage is **lexing** (a.k.a. scanning / tokenizing): chopping a flat string
into the smallest meaningful chunks — *tokens*. `(2 + 3) * 4` is just bytes until the
lexer turns it into `LPAREN NUMBER(2) PLUS NUMBER(3) RPAREN STAR NUMBER(4) EOF`.
[`01_lexer.c`](01_lexer.c) drives the scanner across a few strings:

```
make run1
```
```
source: "(2 + 3) * 4"
  LPAREN
  NUMBER  2
  PLUS
  NUMBER  3
  RPAREN
  STAR
  NUMBER  4
  EOF

source: "print x * x"
  IDENT   "print"
  IDENT   "x"
  STAR
  IDENT   "x"
  EOF
```

Two things to notice: the lexer converts the text `"2"` into the *number* `2`
itself (lexing, not parsing, owns that), and `print` is just an `IDENT` like any
variable — only the parser later decides it's special. The lexer emits a **flat**
stream; precedence is not its job.

## 2. The parser: tokens → AST (with correct precedence)

The **parser** consumes that token stream and builds an **abstract syntax tree**
whose shape encodes how operators nest. We use **recursive descent**: one function
per grammar rule, where the call stack mirrors the grammar.

```
expr   := term (('+' | '-') term)*
term   := factor (('*' | '/') factor)*
factor := NUMBER | IDENT | '(' expr ')'
```

Precedence falls straight out of this layering: `*` and `/` live one level *deeper*
than `+` and `-`, so they bind tighter — no precedence table required.
[`02_parser.c`](02_parser.c) prints each AST fully parenthesised (`make run2`):

```
  2 + 3 * 4      =>  (2 + (3 * 4))
  (2 + 3) * 4    =>  ((2 + 3) * 4)
  10 - 3 - 2     =>  ((10 - 3) - 2)
  8 / 4 / 2      =>  ((8 / 4) / 2)
  1 + 2 * 3 - 4  =>  ((1 + (2 * 3)) - 4)
  x * x + 1      =>  ((x * x) + 1)
```

The headline case: `2 + 3 * 4` parses as `(2 + (3 * 4))` — **the multiply is a
subtree of the add**, so it evaluates first. `10 - 3 - 2` parses left-associatively
as `((10 - 3) - 2)`, the correct `5`, not `(10 - (3 - 2)) = 9`.

## 3. The tree-walking evaluator: AST → result

To **run** the program we walk the AST: to compute a binary op, recursively compute
its two children, then combine. [`03_interpreter.c`](03_interpreter.c) also grows
the language into a real program with **variables** (`x = expr`) and a **`print`**
statement, sharing one environment across lines (`make run3`):

```
=== arithmetic & precedence ===
  2 + 3 * 4        | expr -> 14
  (2 + 3) * 4      | expr -> 20
  100 - 4 * 5 - 2  | expr -> 78
  8 / 4 / 2        | expr -> 1

=== variables & print ===
  x = 6            | x = 6
  y = 7            | y = 7
  print x * y      | print -> 42
  x = x + 1        | x = 7
  print x          | print -> 7

=== a small program ===
  r = 5            | r = 5
  area = 3 * r * r | area = 75
  print area       | print -> 75
```

There it is end to end: `2 + 3 * 4` evaluates to **14** (precedence), `(2 + 3) * 4`
to **20** (parens), and `x = x + 1` reads then updates a variable in the
environment. (This is a *tree-walking evaluator* — the word "eval" is the standard
term for "compute the value of an AST node"; nothing here runs dynamic code.)

## 4. Bytecode + a stack VM: AST → bytecode → result

A tree walker re-walks the tree every time. Faster languages **compile** the AST
once into flat **bytecode**, then run it on a **virtual machine**. Our VM is a
**stack machine**: `PUSH n` pushes a constant; `ADD/SUB/MUL/DIV` pop two operands
and push the result. Compiling a binop is a **post-order** walk (left, right, op),
which is exactly why a stack works. [`04_bytecode_vm.c`](04_bytecode_vm.c) shows the
AST, the disassembly, and the result (`make run4`):

```
=== 2 + 3 * 4 ===
  AST:        (2 + (3 * 4))
  bytecode:
    0000  PUSH 2
    0001  PUSH 3
    0002  PUSH 4
    0003  MUL
    0004  ADD
  result:     14

=== (2 + 3) * 4 ===
  AST:        ((2 + 3) * 4)
  bytecode:
    0000  PUSH 2
    0001  PUSH 3
    0002  ADD
    0003  PUSH 4
    0004  MUL
  result:     20
```

Read the first chunk like a stack trace: push 2, push 3, push 4, `MUL` collapses
`3 4 → 12`, `ADD` collapses `2 12 → 14`. The parens version emits `ADD` *before* the
final `MUL`, giving `20`. Same source operators, different instruction order —
that's the compiler encoding precedence into a linear program.

> **Memory:** every demo `ast_free()`s the trees it builds and `chunk_free()`s its
> bytecode, so there are no leaks (the constructors `malloc`/`calloc`, the tree is
> freed post-order). This is the honest, non-arena approach; a real compiler often
> uses an *arena* allocator and frees everything at once instead.

---

## 5. Exercises

Each lives in `exercises/` with `// TODO`s; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`. Each is a
self-contained pipeline so you can edit the lexer/parser/VM directly.

### Exercise 40.1 — Add the `%` modulo operator end to end  (`make ex1`)
Thread a new operator `%` through the **lexer, parser, and evaluator** in
[`exercises/ex1_modulo.c`](exercises/ex1_modulo.c) (three `// TODO`s). It shares the
precedence of `*` and `/`. Expected (`make sol1`):
```
  17 % 5         = 2
  2 + 17 % 5     = 4
  (2 + 17) % 5   = 4
  20 % 6 * 2     = 4
```
`2 + 17 % 5 == 4` proves `%` binds tighter than `+`.

### Exercise 40.2 — Add unary minus  (`make ex2`)
Support a leading `-` (e.g. `-5`, `3 * -2`, `--5`) in the **parser and evaluator**
in [`exercises/ex2_unary_minus.c`](exercises/ex2_unary_minus.c) (two `// TODO`s; an
`N_NEG` node is provided). Expected (`make sol2`):
```
  -5             = -5
  3 * -2         = -6
  10 - -4        = 14
  --5            = 5
  -(2 + 3)       = -5
```

### Exercise 40.3 — Add a `NEG` bytecode op to the VM  (`make ex3`)
The parser already builds unary-minus nodes; teach the **compiler and stack VM** a
new `OP_NEG` instruction (pop one, push its negation) in
[`exercises/ex3_vm_neg.c`](exercises/ex3_vm_neg.c) (four `// TODO`s). Expected
(`make sol3`):
```
=== -5 ===
    0000  PUSH 5
    0001  NEG
  result: -5

=== 3 * -2 ===
    0000  PUSH 3
    0001  PUSH 2
    0002  NEG
    0003  MUL
  result: -6
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **Lexing** | Turning raw text into typed tokens is every compiler's first stage; doing it by hand demystifies regex/lexer generators |
| **Recursive-descent parsing** | One function per grammar rule, call stack = grammar — the most readable way to parse, used in real compilers (clang, Go) |
| **Precedence & associativity** | Layering the grammar makes `2 + 3 * 4 == 14` and `8 / 4 / 2 == 1` fall out automatically — no precedence table |
| **ASTs** | A program is a tree; building, walking, pretty-printing, and freeing it are the core skills for any language tool |
| **Tree-walking evaluation** | The simplest way to *run* a language; variables + `print` turn expressions into a real little program |
| **Bytecode & a stack VM** | Compile once, run flat instructions on a stack — the model behind Python, the JVM, and Nand2Tetris's VM |

## Further reading

- **Crafting Interpreters** — Robert Nystrom (free online; this module is its arc in
  miniature — a tree-walking interpreter then a bytecode VM): https://craftinginterpreters.com/
- **Nand2Tetris, projects 6–11** — assembler, VM translator, and a compiler for the
  Jack language, built on the CPU from Module 29: https://www.nand2tetris.org/
- **MIT 6.035 — Computer Language Engineering** (a full optimizing compiler course):
  https://ocw.mit.edu/courses/6-035-computer-language-engineering-spring-2010/
- **The "Dragon Book"** — *Compilers: Principles, Techniques, and Tools* (Aho,
  Lam, Sethi, Ullman) — the classic comprehensive reference.

**Next:** Module 41 — Networking Deep-Dive — TCP/IP internals, routing, and RPC in
C, extending [Module 21](../21_networking_and_packets/). *(Not yet built — see
[the track plan](../cs-foundations-track.md).)* → ../41_networking/README.md
