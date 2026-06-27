# SOLUTION 32.3 — Trace a stack frame

**1. How `sp` moves.** `stp x29, x30, [sp, #-16]!` pre-decrements `sp` by **16 bytes**
before storing. The stack **grows downward** (toward lower addresses), so allocating
a frame means subtracting from `sp`. 16 bytes holds the two 8-byte registers and also
keeps `sp` 16-byte aligned, which the arm64 ABI requires.

**2. Which is which, and where.** `stp x29, x30` stores the pair in ascending address
order, so relative to the **new** `sp`:

- `x29` (the **saved frame pointer** — the caller's `x29`) is stored at `[sp, #0]`.
- `x30` (the **saved return address** — the `lr` value pointing just after the `bl`
  that called `_outer`) is stored at `[sp, #8]`.

So: return address at offset **+8**, saved frame pointer at offset **+0** from `sp`.

**3. Line (B), `mov x29, sp`.** This sets the frame pointer to the base of the new
frame. With `x29` fixed for the whole function, locals and saved values can be
addressed at constant offsets from `x29` even as `sp` shifts (e.g. if the body pushes
more). The chain of saved `x29` values also lets a debugger walk the call stack
(`bt` in lldb/gdb follows exactly these saved frame pointers).

**4. The return.** `ldp x29, x30, [sp], #16` reloads the caller's frame pointer into
`x29` and the saved return address into `x30`, then post-increments `sp` by 16 —
deallocating the frame and restoring `sp` to what the caller had. `ret` then branches
to the address now in `x30`, landing back in the caller right after its `bl _outer`.

If a non-leaf function **skipped** saving `x30`: its own `bl _inner` would overwrite
`x30` with the address inside `_outer` (just after that `bl`). When `_outer` later did
`ret`, it would branch back into *itself* instead of returning to its caller — an
infinite loop or a crash. Leaf functions (like `add_asm`/`max2` in this module) make
no `bl`, so `x30` is never clobbered and they need no frame at all.
