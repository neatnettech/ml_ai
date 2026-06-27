# Exercise 36.3 — Add a system call to xv6  (guided, xv6 tree + qemu)

> **This exercise is xv6/RISC-V-gated.** It is done *inside the xv6-riscv source tree*
> and verified by booting xv6 under `qemu-system-riscv64`. It does **not** build or run
> with this module's `Makefile` — there is no `make ex3`. See PART B of the README for
> how to clone xv6 and install the RISC-V toolchain + qemu.

## The task

Add a new system call **`getppid()`** to xv6 — it returns the PID of the calling
process's parent (the xv6 kernel already tracks `p->parent`). Then write a small user
program that calls it and prints the result.

> A common alternative chosen for the MIT 6.1810 labs is **`trace`** (a syscall-tracing
> mask) or **`sysinfo`** (free memory + process count). `getppid` is the smallest
> end-to-end example and exercises every file a real syscall touches.

A system call in xv6 crosses the user→kernel boundary, so adding one means touching
**both sides** plus the dispatch table that connects them. Your job: figure out *which
files* and *what to add in each*, and *why*.

## Deliverable

Write up, in your own words, the ordered list of edits — file by file — needed to add
`getppid`. For each file say **what** you add and **why it is required**. Then describe
how you would test it under qemu.

Use these prompts (fill in the "what/why" yourself; the worked answer is in
`../solutions/ex3_add_syscall.md`):

1. **`user/user.h`** — what declaration goes here, and who reads it?
2. **`user/usys.pl`** — what does this Perl script generate, and what line do you add?
   (It emits `user/usys.S`, the stubs that issue the `ecall` trap.)
3. **`kernel/syscall.h`** — what symbol do you add, and what is it used for?
4. **`kernel/syscall.c`** — there are *two* edits here. What are they? (Hint: an
   `extern` declaration and an entry in the `syscalls[]` dispatch array.)
5. **`kernel/sysproc.c`** — what function do you implement, and how does it read the
   parent PID? (Hint: `myproc()`, the `struct proc`, `p->parent`, and locking.)
6. **A new `user/getppid.c`** + the **`UPROGS`** list in the **`Makefile`** — why is
   each needed for the program to appear in xv6's shell?

Finally: **how do you test it?** (Boot with `make qemu`, run your program, compare to
the PID the parent shell reports.)

## Why this is a paper exercise here

The edits require the xv6 tree, the RISC-V cross-compiler, and qemu to assemble the
`ecall` stubs, link the kernel, and boot. We don't fake that output. Do the write-up
now; do the real edits when you have the toolchain from PART B installed.
