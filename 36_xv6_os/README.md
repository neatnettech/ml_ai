# Module 36 — Operating Systems with xv6

**Purpose:** An operating system is the program that turns raw hardware into the
abstractions every other program assumes: **processes**, **system calls**, **pipes**,
a **scheduler**, and **virtual memory**. The best way to *understand* a kernel is to
read and extend a small real one — and **xv6** (MIT 6.1810) is exactly that: a
teaching reimplementation of Unix v6 in ~9,000 lines of C + RISC-V assembly, small
enough to read in a weekend. This module has two halves: **PART A** makes the OS
abstractions concrete with tiny C programs that run *natively on this Mac* (fork+exec,
pipes, raw syscalls, a 50-line shell), and **PART B** is a lab guide for building and
extending xv6 itself under `qemu-system-riscv64`.

> **Honesty about what runs where.** PART A is portable POSIX C and runs natively here
> — every output block below is real. **PART B (xv6 proper) does NOT run on this arm64
> Mac as a normal binary**: it targets RISC-V and boots under qemu with a cross-toolchain.
> We do **not** fake xv6 output — PART B tells you exactly how to run it yourself.

**Prerequisites:** Module 34 (linking & loading — how a program image becomes a running
process) and Module 35 (virtual memory — page tables, which xv6's `kernel/vm.c`
implements). Module 37 (concurrency) is helpful for *why* the scheduler interleaves
processes, but is not required.

**What you'll learn:**
- How a new process is born: **`fork()` + `exec()` + `wait()`** — and why it's *two*
  calls, not one (the structure of every Unix shell, including xv6's `user/sh.c`)
- **Pipes**: a kernel buffer + `dup2()` is the whole mechanism behind `ls | wc`
- **System calls**: how a library call traps from user mode into the kernel (RISC-V
  `ecall`), and how xv6 dispatches it (`kernel/syscall.c` → `sys_*`)
- How to **read and extend a real kernel**: add a user program, add a *new system call*,
  and find the scheduler (`kernel/proc.c`) and page tables (`kernel/vm.c`)

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

**PART A** runs **natively on Apple Silicon** — you only need `clang` + `make` (Xcode
Command Line Tools):

```bash
make run     # build + run all four native demos
```

**PART B (xv6)** needs **qemu + a RISC-V cross-toolchain** — see the
[setup notes](../28_bits_and_bytes/setup/README.md) (qemu is in the Brewfile) and
PART B below. `make help-xv6` prints the quick pointer.

---

# PART A — the OS abstractions, natively (runs here, real output)

These four programs use POSIX syscalls, so they run on this Mac (and Linux, and the
x86-64 container). They are the *same* abstractions xv6 implements — we note the
matching xv6 file for each.

## 1. fork / exec / wait — how a process is born

A new program does **not** start with one "run this" call. Instead the kernel offers
two primitives: **`fork()`** clones the current process (returning twice — `0` in the
child, the child's PID in the parent), and **`exec()`** *replaces* a process's image
with a new program. The shell forks, the child runs the command, the parent
`wait()`s. [`01_fork_exec.c`](01_fork_exec.c) (`make run1`) — xv6: `sys_fork`,
`sys_exec`, `sys_wait` in `kernel/sysproc.c`:

```
=== fork / exec / wait ===
parent: my pid is 35717
child : my pid is 35718, my parent is 35717
child : replacing my image with /bin/echo ...
hello from the replaced program
parent: forked a child with pid 35718, now waiting...
parent: child 35718 exited with status 0
parent: done.
```

Two gotchas this demo bakes in: after a successful image swap the following lines
**never run** (the old program is gone), and you must **`fflush` before `fork`** or a
buffered `stdout` gets duplicated into the child and printed twice.

## 2. Pipes — `ls | wc` from first principles

A **pipe** is a kernel-owned buffer with a read end and a write end. Add `fork()` (two
processes) and `dup2()` (point a process's stdout/stdin at the pipe) and you have a
shell pipeline. [`02_pipes.c`](02_pipes.c) (`make run2`) shows the raw primitive and a
real two-process pipeline — xv6: `kernel/pipe.c`, `sys_pipe`:

```
=== part 1: parent writes, child reads ===
child : read 34 bytes from the pipe: "data flowing through kernel memory"

=== part 2: pipeline equivalent to  printf 'a\nb\nc\n' | wc -l ===
       3
(the line above, printed by wc, should be 3)
```

Key rule: the parent must **close both pipe ends**, or the reader never sees EOF and
hangs forever — the single most common pipe bug.

## 3. System calls — where the C library hits the kernel

`printf` is a library function; underneath it calls **`write()`**, a *system call* — the
controlled doorway into the kernel. The CPU executes a trap instruction (RISC-V
`ecall`), switches to supervisor mode, runs kernel code, and returns.
[`03_syscalls.c`](03_syscalls.c) (`make run3`) uses the raw syscalls directly so you
*see* the boundary — xv6: `user/usys.S` (`ecall`) → `kernel/trap.c` →
`kernel/syscall.c` → `sys_*`:

```
=== raw syscalls (no stdio) ===
getpid() trapped into the kernel -> pid 35723
first line of my own source via open/read/close:
  // Module 36 — Demo 3: system calls — where the C library bottoms out in th

tip: 'strace' (Linux) or 'sudo dtruss' (macOS) prints every syscall this
     program makes. xv6's equivalent is reading kernel/syscall.c.
```

To watch syscalls live: `strace ./bin/03_syscalls` on Linux, or `sudo dtruss
./bin/03_syscalls` on macOS (needs sudo; System Integrity Protection blocks tracing of
*system* binaries, but your own binary is fine).

## 4. A tiny shell — `user/sh.c` condensed

A shell is just a loop: prompt → read a line → tokenize → `fork` → child runs the
program → parent `wait`s. [`04_shell.c`](04_shell.c) is that loop in ~50 lines — the
skeleton of xv6's `user/sh.c`. `make run4` runs a canned, self-terminating script so
it's verifiable without a human at the keyboard (interactively, `./bin/04_shell` reads
from the terminal and quits on Ctrl-D):

```
hello from tinysh
the next line lists this directory:
01_fork_exec.c
02_pipes.c
03_syscalls.c
04_shell.c
Makefile
bin
exercises
solutions
tinysh: command not found: nope_not_a_real_command
tinysh$ echo hello from tinysh
tinysh$ echo the next line lists this directory:
tinysh$ ls
tinysh$ nope_not_a_real_command
tinysh$ exit
```

(`exit` is a *builtin* — it must run in the shell process itself, not a child, which is
why xv6 handles `cd` the same way.) Exercise 36.1 extends this with a single `|` pipe.

---

# PART B — xv6 proper (qemu + RISC-V — NOT run here)

xv6 boots under `qemu-system-riscv64`; it is **not** an arm64 macOS binary. The output
in this section is **not shown** because we don't fake it — run these steps yourself.

## Setup

```bash
# 1. qemu (in the Brewfile):
brew install qemu

# 2. a RISC-V cross-toolchain providing riscv64-unknown-elf-gcc:
#    macOS (Homebrew tap):
brew tap riscv-software-src/riscv && brew install riscv-tools
#    Debian/Ubuntu alternative:
#    sudo apt install gcc-riscv64-unknown-elf gdb-multiarch qemu-system-misc

# 3. get xv6 and boot it:
git clone https://github.com/mit-pdos/xv6-riscv.git
cd xv6-riscv
make qemu          # cross-compiles the kernel + userland, boots xv6 in qemu
#    at the "$ " prompt you have a real Unix shell: try  ls, cat, echo, grep
#    EXIT qemu with:  Ctrl-a  then  x
```

`make qemu` is gated entirely on having the RISC-V compiler + qemu installed; without
them it fails at compile time. `make help-xv6` prints this pointer.

## The canonical xv6 labs (done IN the xv6 tree)

These are the exercises you do *inside* `xv6-riscv`, mirroring the MIT 6.1810 labs.
Each references **real xv6 file names**:

- **Add a user program (`sleep`).** Write `user/sleep.c` that parses an integer
  argument and calls the existing `sleep()` syscall, then add `_sleep` to `UPROGS` in
  the `Makefile`. Warm-up: no kernel changes, just the userland + build wiring.
- **Add a new system call.** The 6.1810 "syscall" lab adds `trace` (a per-process
  syscall-tracing mask) and `sysinfo` (free memory + process count). The files you
  touch: `user/user.h`, `user/usys.pl` (generates the `ecall` stubs in `user/usys.S`),
  `kernel/syscall.h` (the call number), `kernel/syscall.c` (the dispatch table), and
  `kernel/sysproc.c` (the implementation). **Exercise 36.3 walks this through for
  `getppid`** — see [`exercises/ex3_add_syscall.md`](exercises/ex3_add_syscall.md).
- **Understand the scheduler.** Read `kernel/proc.c`: the `scheduler()` round-robin
  loop, `swtch()` (the context switch in `kernel/swtch.S`), `sched()`, `yield()`, and
  the `struct proc` state machine (`RUNNABLE`/`RUNNING`/`SLEEPING`).
- **Understand page tables.** Read `kernel/vm.c`: `walk()` (RISC-V three-level page-table
  walk), `mappages()`, `kvmmap()` (the kernel page table), and how each process gets its
  own address space — the direct continuation of Module 35.

The xv6 book (Further reading) is the companion text: each chapter maps to these files.

---

## Exercises

Native exercises live in `exercises/` with a `// TODO`; reference answers are in
`solutions/`. Build & run your attempt with `make exN`, the solution with `make solN`.
Exercise 36.3 is an xv6/RISC-V-gated **paper** exercise (markdown, no make target).

### Exercise 36.1 — Add a `|` pipe to the tiny shell  (native, `make ex1`)
Implement `run_pipe()` in [`exercises/ex1_pipe_shell.c`](exercises/ex1_pipe_shell.c):
`pipe()` + two `fork()`s + `dup2()` to run `left | right`. Expected (`make sol1`):
```
$ echo hi | wc -c ->        3
$ printf a\nb\nc\n | wc -l ->        3
$ ls | wc -l ->        8
```
(The last number counts entries in this directory, so it may differ for you.)

### Exercise 36.2 — Run a command, return its exit status  (native, `make ex2`)
Implement `run_status()` in [`exercises/ex2_run_status.c`](exercises/ex2_run_status.c)
(`fork`/`exec`/`waitpid`), verified on the canonical `/usr/bin/true` and
`/usr/bin/false`. Expected (`make sol2`):
```
ok
run_status(/usr/bin/true ) = 0
run_status(/usr/bin/false) = 1
run_status(/bin/echo ok  ) = 0
```
(`ok` is printed by the child `echo` and appears first.)

### Exercise 36.3 — Add a system call to xv6  (xv6/RISC-V, guided write-up)
A **paper / design** exercise — it requires the xv6 tree + qemu, so there is no make
target. In [`exercises/ex3_add_syscall.md`](exercises/ex3_add_syscall.md) you work out
which files to edit to add `getppid` and *why*. The "solution" is the full walkthrough
in [`solutions/ex3_add_syscall.md`](solutions/ex3_add_syscall.md).

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **fork / exec / wait** | A process is *cloned* then *replaced* — two calls, not one; the basis of every shell and of xv6's `user/sh.c` |
| **Pipes + dup2** | A kernel buffer wired onto stdin/stdout is the entire mechanism behind `ls \| wc`; forget to close an end and it hangs |
| **System calls** | Library calls bottom out in syscalls that *trap* user→kernel (RISC-V `ecall`); xv6 dispatches them in `kernel/syscall.c` |
| **A shell as a loop** | prompt → read → fork → exec → wait; builtins (`exit`, `cd`) must run in the shell process itself |
| **Reading a real kernel** | xv6 is small enough to read end-to-end; adding a syscall touches a fixed set of files (user stub → number → dispatch → impl) |
| **Scheduler & page tables** | `kernel/proc.c` (round-robin, `swtch`) and `kernel/vm.c` (`walk`, `mappages`) connect Modules 35–37 to a working OS |

## Further reading

- **The xv6 book — *xv6: a simple, Unix-like teaching operating system* (rev4)** — the
  companion text; each chapter maps to the kernel files above:
  https://pdos.csail.mit.edu/6.1810/2024/xv6/book-riscv-rev4.pdf
- **MIT 6.1810 (Operating System Engineering)** — the course, with the full lab series
  (syscall, pgtbl, traps, scheduling, fs) and the xv6-riscv source:
  https://pdos.csail.mit.edu/6.1810/2024/xv6.html
- **xv6-riscv source** (clone this for PART B): https://github.com/mit-pdos/xv6-riscv
- **OSTEP — *Operating Systems: Three Easy Pieces* (Arpaci-Dusseau)** — the free,
  outstanding OS textbook covering virtualization, concurrency, and persistence:
  https://pages.cs.wisc.edu/~remzi/OSTEP/

**Next:** Module 37 — Concurrency — spawn POSIX threads, *watch* a data race lose
updates, then fix it three ways (mutex, condition variable, atomics) and see how a
deadlock arises — the mechanics behind the scheduler you just met.
→ [../37_concurrency/README.md](../37_concurrency/README.md)
