// Module 36 — Demo 2: pipe() + fork()  (how `ls | wc` works under the hood)
//
// A pipe is a kernel-owned buffer with two ends: write to fd[1], read from fd[0].
// Combined with fork() (so both halves run as separate processes) and dup2() (to
// wire a process's stdout/stdin onto the pipe), this is the entire mechanism behind
// a shell pipeline. xv6 implements pipes in kernel/pipe.c and the syscall in
// sys_pipe (kernel/sysproc.c); user/sh.c builds pipelines exactly like this.
//
// We build TWO things:
//   Part 1: a simple parent-writes / child-reads pipe (the raw primitive).
//   Part 2: a real 2-process pipeline equivalent to:  printf "..." | wc -l
//
// Build & run: make run2   — read alongside README.md PART A §2.

#define _DARWIN_C_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>     // pipe, fork, dup2, read, write, close
#include <sys/wait.h>

// Part 1 — the raw primitive: parent writes a message, child reads it.
static void simple_pipe(void) {
    printf("=== part 1: parent writes, child reads ===\n");
    int fd[2];                       // fd[0] = read end, fd[1] = write end
    if (pipe(fd) < 0) { perror("pipe"); exit(1); }

    fflush(stdout);                  // flush before fork (see note in 01_fork_exec.c)
    pid_t pid = fork();
    if (pid < 0) { perror("fork"); exit(1); }

    if (pid == 0) {
        // child: only reads, so close the write end.
        close(fd[1]);
        char buf[128];
        ssize_t n = read(fd[0], buf, sizeof buf - 1);
        if (n > 0) {
            buf[n] = '\0';
            printf("child : read %zd bytes from the pipe: \"%s\"\n", n, buf);
            fflush(stdout);   // _exit() below does NOT flush stdio buffers
        }
        close(fd[0]);
        _exit(0);
    }

    // parent: only writes, so close the read end.
    close(fd[0]);
    const char *msg = "data flowing through kernel memory";
    write(fd[1], msg, strlen(msg));
    close(fd[1]);                    // EOF for the reader
    wait(NULL);
}

// Part 2 — a real pipeline:  (left) | (right)
// left  process: writes some lines to the pipe (stands in for `printf`/`ls`).
// right process: runs `wc -l` with its stdin REPLACED by the pipe's read end.
static void pipeline_wc(void) {
    printf("\n=== part 2: pipeline equivalent to  printf 'a\\nb\\nc\\n' | wc -l ===\n");
    int fd[2];
    if (pipe(fd) < 0) { perror("pipe"); exit(1); }

    fflush(stdout);                  // flush before forking either pipeline stage
    pid_t right = fork();            // the consumer:  wc -l
    if (right < 0) { perror("fork"); exit(1); }
    if (right == 0) {
        // Replace stdin (fd 0) with the pipe's read end, then become `wc`.
        dup2(fd[0], STDIN_FILENO);
        close(fd[0]);
        close(fd[1]);                // wc never writes to the pipe
        char *args[] = {"wc", "-l", NULL};
        execvp("wc", args);
        perror("execvp wc");
        _exit(127);
    }

    pid_t left = fork();             // the producer
    if (left < 0) { perror("fork"); exit(1); }
    if (left == 0) {
        // Replace stdout (fd 1) with the pipe's write end, then emit lines.
        dup2(fd[1], STDOUT_FILENO);
        close(fd[0]);
        close(fd[1]);
        printf("a\nb\nc\n");         // three lines -> wc -l should print 3
        fflush(stdout);
        _exit(0);
    }

    // parent: holds neither end open, or wc would never see EOF.
    close(fd[0]);
    close(fd[1]);
    wait(NULL);
    wait(NULL);
    printf("(the line above, printed by wc, should be 3)\n");
}

int main(void) {
    simple_pipe();
    pipeline_wc();
    return 0;
}
