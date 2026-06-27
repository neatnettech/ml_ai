# Exercise 32.3 — Trace a stack frame (paper exercise)

No code to write — read the prologue/epilogue of a non-leaf arm64 function and
identify where the **saved return address** and **saved frame pointer** live. Then
check `../solutions/ex3_stack_frame.md`.

A *non-leaf* function (one that calls another function) must preserve the link
register `x30` (the return address) across that inner call, because `bl` overwrites
`x30`. It also saves the caller's frame pointer `x29`. Here is the arm64 prologue and
epilogue clang emits for such a function (the body, which makes the inner call, is
elided):

```asm
_outer:
        stp     x29, x30, [sp, #-16]!   // (A)  prologue
        mov     x29, sp                 // (B)
        // ... body: sets up args, executes `bl _inner`, uses the result ...
        ldp     x29, x30, [sp], #16     // (C)  epilogue
        ret                             // (D)
```

`stp` = store pair, `ldp` = load pair. The `[sp, #-16]!` form is **pre-indexed**: it
subtracts 16 from `sp` *first*, then stores; the trailing `!` writes the updated `sp`
back. The `[sp], #16` form is **post-indexed**: it loads, then adds 16 to `sp`.

**Questions:**

1. After line (A) executes, by how many bytes has `sp` moved, and in which direction
   (does the stack grow up or down)?
2. Of the two saved registers, which one is the **return address** and which is the
   **saved frame pointer**? At what offset from the *new* `sp` does each sit?
3. What does line (B) accomplish, and why is `x29` useful inside the body?
4. Lines (C)–(D): explain how the function returns to its caller. What would break if
   a non-leaf function *skipped* saving `x30`?
