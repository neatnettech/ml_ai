# SOLUTION 36.3 — Adding `getppid()` to xv6 — the walkthrough

> File names below refer to the **xv6-riscv** tree (https://github.com/mit-pdos/xv6-riscv).
> This is the design write-up; the actual build/boot is PART B (qemu + RISC-V toolchain).
> The same recipe adds *any* syscall — only step 5 (the kernel implementation) changes.

A syscall has to be visible to the user-side C, reachable through the trap stub, and
dispatched on the kernel side. That's why a one-function feature spans ~6 files: each
file closes one link in user → `ecall` trap → kernel dispatch → kernel code → return.

## The edits, in order

### 1. `user/user.h` — the user-facing prototype
Add the C declaration so user programs (and the compiler) know the call exists:
```c
int getppid(void);
```
Every user program `#include`s `user.h`; without this the program won't compile.

### 2. `user/usys.pl` — generate the trap stub
`usys.pl` is a Perl script run during the build to emit `user/usys.S`, the assembly
stubs. Each stub loads the syscall number into register `a7` and executes `ecall`
(the RISC-V instruction that traps into the kernel). Add one line:
```perl
entry("getppid");
```
This produces a `getppid:` stub in `usys.S`. **Why:** the user-side function is *not*
real code — it's just "set a7, `ecall`, return". This script writes that for you.

### 3. `kernel/syscall.h` — assign a syscall number
The number in `a7` is how the kernel knows *which* call was requested. Add the next
free number:
```c
#define SYS_getppid 22   // use whatever the next unused value is
```
Both the generated stub (step 2) and the dispatch table (step 4) key off this constant.

### 4. `kernel/syscall.c` — wire it into the dispatch table  (TWO edits)
The kernel's trap handler indexes an array `syscalls[]` by the number in `a7`.
(a) Declare the kernel implementation (defined in step 5):
```c
extern uint64 sys_getppid(void);
```
(b) Add it to the dispatch array, keyed by the constant from step 3:
```c
static uint64 (*syscalls[])(void) = {
    // ... existing entries ...
    [SYS_getppid] sys_getppid,
};
```
**Why:** without the array entry, `ecall` with that number would hit the kernel's
"unknown sys call" path and fail.

### 5. `kernel/sysproc.c` — the kernel implementation
This is the only part that's actually about *getppid* specifically. Read the parent
PID out of the current process structure:
```c
uint64
sys_getppid(void)
{
    struct proc *p = myproc();      // the process that trapped
    int ppid;
    acquire(&wait_lock);            // p->parent is protected by wait_lock in xv6
    if (p->parent)
        ppid = p->parent->pid;
    else
        ppid = -1;                  // init has no parent
    release(&wait_lock);
    return ppid;
}
```
Syscall implementations return a `uint64`; the trap return path puts it in `a0`, which
the user-side stub returns as the function's result. **Why the lock:** `p->parent` can
change concurrently (e.g. during `exit`/`reparent`), so xv6 guards it with `wait_lock`.

### 6. A user program + the Makefile
Create `user/getppid.c`:
```c
#include "kernel/types.h"
#include "user/user.h"
int main(void) {
    printf("my parent pid is %d\n", getppid());
    exit(0);
}
```
Then add it to the `UPROGS` list in the top-level **`Makefile`** so it gets compiled
and bundled into the xv6 filesystem image:
```make
UPROGS=\
    ...\
    $U/_getppid\
```
**Why:** xv6's shell can only run programs that exist in its filesystem image; `UPROGS`
is what populates that image at build time.

## Testing it under qemu

```bash
make qemu
# at the xv6 prompt:
$ getppid
my parent pid is 2        # 2 is the shell (sh); 1 is init
```
Sanity check: the number should match the PID of the shell that launched it. Exit qemu
with `Ctrl-a x`.

## The mental model

```
user program  --calls-->  getppid()           (user.h prototype)
                          usys.S stub: a7 = SYS_getppid; ecall   (TRAP -> supervisor mode)
kernel trap handler --indexes syscalls[a7]-->  sys_getppid()     (syscall.c, sysproc.c)
                                               returns ppid in a0
user program  <--returns-- a0
```
Every syscall you ever add follows this exact path; only step 5 carries the new logic.
