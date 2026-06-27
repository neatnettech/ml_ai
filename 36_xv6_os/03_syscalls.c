// Module 36 — Demo 3: system calls — where the C library bottoms out in the kernel
//
// printf() is a LIBRARY function. Eventually it must ask the kernel to actually put
// bytes on the terminal, and it does so via the write() SYSTEM CALL. A syscall is the
// controlled doorway from user mode into the kernel: the CPU executes a special trap
// instruction (RISC-V `ecall`, x86-64 `syscall`), switches to supervisor mode, runs
// kernel code, then returns. xv6's path is: user/usys.S issues `ecall` -> kernel trap
// handler (kernel/trampoline.S, kernel/trap.c) -> kernel/syscall.c dispatches by number
// -> the sys_* function (e.g. sys_write in kernel/sysfile.c).
//
// This demo deliberately uses the RAW syscalls (write/open/read/close/getpid) instead
// of stdio, so you SEE the boundary. Build & run: make run3 — README.md PART A §3.

#define _DARWIN_C_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>     // write, read, close, getpid
#include <fcntl.h>      // open, O_* flags

int main(void) {
    // 1) write(2, ...) — talk to stderr (fd 2) with NO stdio buffering in between.
    //    This is the single syscall printf ultimately relies on.
    const char *banner = "=== raw syscalls (no stdio) ===\n";
    write(STDERR_FILENO, banner, strlen(banner));

    // 2) getpid() — a tiny syscall that just reads a kernel-held value (this process's id).
    pid_t me = getpid();
    char line[64];
    int len = snprintf(line, sizeof line, "getpid() trapped into the kernel -> pid %d\n", (int)me);
    write(STDERR_FILENO, line, (size_t)len);

    // 3) open / read / close — the file syscalls. Open this very source file and show
    //    its first line, using only kernel calls (no fopen/fgets).
    const char *path = "03_syscalls.c";
    int fd = open(path, O_RDONLY);
    if (fd < 0) {
        const char *err = "(could not open 03_syscalls.c; run from the module dir)\n";
        write(STDERR_FILENO, err, strlen(err));
        return 1;
    }

    char buf[80];
    ssize_t n = read(fd, buf, sizeof buf - 1);   // read() = one trap into the kernel
    if (n > 0) {
        // print up to the first newline so the output is tidy
        char *nl = memchr(buf, '\n', (size_t)n);
        size_t show = nl ? (size_t)(nl - buf) : (size_t)n;
        write(STDERR_FILENO, "first line of my own source via open/read/close:\n  ", 51);
        write(STDERR_FILENO, buf, show);
        write(STDERR_FILENO, "\n", 1);
    }
    close(fd);                                    // close() = another trap

    // Note on observing syscalls live:
    //   Linux:  strace ./bin/03_syscalls          (lists every syscall + args)
    //   macOS:  sudo dtruss ./bin/03_syscalls     (needs sudo; System Integrity
    //           Protection may block tracing of system binaries — your own binary is fine)
    const char *tip =
        "\ntip: 'strace' (Linux) or 'sudo dtruss' (macOS) prints every syscall this\n"
        "     program makes. xv6's equivalent is reading kernel/syscall.c.\n";
    write(STDERR_FILENO, tip, strlen(tip));
    return 0;
}
