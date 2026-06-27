// Module 36 — Demo 1: fork() + exec() + wait()  (the heart of every Unix kernel)
//
// xv6's kernel gives user programs exactly this trio. A new process is NOT created
// with a name + arguments in one call; instead:
//   1. fork()  duplicates the current process -> two identical processes (parent+child)
//   2. exec()  REPLACES the child's program image with a new one (here: /bin/echo)
//   3. wait()  lets the parent block until the child finishes and collect its status
// This is precisely how a shell launches a command (see 04_shell.c) and is the
// structure of xv6's user/sh.c. We use the POSIX calls so it runs natively on this
// Mac; xv6 implements the SAME syscalls in kernel/sysproc.c (sys_fork, sys_exec, sys_wait).
//
// Build & run: make run1   — read alongside README.md PART A §1.

#define _DARWIN_C_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>     // fork, execvp, getpid, getppid
#include <sys/wait.h>   // wait, WIFEXITED, WEXITSTATUS

int main(void) {
    printf("=== fork / exec / wait ===\n");
    printf("parent: my pid is %d\n", (int)getpid());

    // Flush stdout BEFORE forking. When stdout is not a terminal it is fully
    // buffered, and fork() would otherwise duplicate the unflushed buffer into the
    // child — printing everything twice. (A subtle, real Unix gotcha.)
    fflush(stdout);

    pid_t pid = fork();          // <-- one call, returns TWICE
    if (pid < 0) {
        perror("fork");
        return 1;
    }

    if (pid == 0) {
        // ---- child path: fork() returned 0 here ----
        printf("child : my pid is %d, my parent is %d\n",
               (int)getpid(), (int)getppid());
        printf("child : replacing my image with /bin/echo ...\n");
        fflush(stdout);

        // execvp REPLACES this process image. On success it NEVER returns —
        // the lines after it run only if the call failed.
        char *args[] = {"echo", "hello from the replaced program", NULL};
        execvp("echo", args);

        perror("execvp");   // only reached if the image swap failed
        _exit(127);
    }

    // ---- parent path: fork() returned the child's pid here ----
    printf("parent: forked a child with pid %d, now waiting...\n", (int)pid);

    int status = 0;
    pid_t done = wait(&status);  // block until the child exits; reap it
    if (done < 0) {
        perror("wait");
        return 1;
    }

    if (WIFEXITED(status)) {
        printf("parent: child %d exited with status %d\n",
               (int)done, WEXITSTATUS(status));
    } else {
        printf("parent: child %d did not exit normally\n", (int)done);
    }

    printf("parent: done.\n");
    return 0;
}
