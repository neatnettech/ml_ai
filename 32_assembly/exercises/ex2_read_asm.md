# Exercise 32.2 — Read the assembly, predict the return value (paper exercise)

This one is read-only: no code to write. Below is a function compiled with
`clang -O1 -S` for **arm64**. Trace it by hand and answer the questions. Then check
`../solutions/ex2_read_asm.md`.

The original C prototype was:

```c
long mystery(long n);
```

Generated arm64 assembly (`clang -O1 -S`):

```asm
_mystery:
        mov     x8, #0          // x8 = 0          (an accumulator)
        mov     x9, #1          // x9 = 1          (a counter, i)
Lloop:
        cmp     x9, x0          // compare i (x9) with n (x0)
        b.gt    Ldone           // if i > n, leave the loop
        add     x8, x8, x9      // acc += i
        add     x9, x9, #2      // i += 2
        b       Lloop
Ldone:
        mov     x0, x8          // return value = acc
        ret
```

**Questions:**

1. `n` arrives in which register, and the return value leaves in which register?
2. In plain English, what does the loop compute as a function of `n`?
3. What does `mystery(6)` return? Trace each iteration (value of `i` and `acc`).
4. What does `mystery(1)` return?
