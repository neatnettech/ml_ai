// SOLUTION 36.1 — Add a single `|` pipe to the tiny shell  (native; make sol1)
//
// run_pipe() below is the worked answer: pipe() + two forks + dup2() + two waits.
// This is the same wiring xv6's user/sh.c performs for a PIPE node.

#define _DARWIN_C_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>

#define MAXARGS 32

static int tokenize(char *line, char *argv[], int max) {
    int argc = 0;
    char *p = line;
    while (argc < max - 1) {
        while (*p == ' ' || *p == '\t' || *p == '\n') *p++ = '\0';
        if (*p == '\0') break;
        argv[argc++] = p;
        while (*p && *p != ' ' && *p != '\t' && *p != '\n') p++;
    }
    argv[argc] = NULL;
    return argc;
}

static void run_simple(char *line) {
    char *argv[MAXARGS];
    if (tokenize(line, argv, MAXARGS) == 0) return;
    pid_t pid = fork();
    if (pid == 0) {
        execvp(argv[0], argv);
        fprintf(stderr, "exec failed: %s\n", argv[0]);
        _exit(127);
    }
    waitpid(pid, NULL, 0);
}

// Run  left | right.
static void run_pipe(char *left, char *right) {
    char *largv[MAXARGS], *rargv[MAXARGS];
    tokenize(left, largv, MAXARGS);
    tokenize(right, rargv, MAXARGS);

    int fd[2];
    if (pipe(fd) < 0) { perror("pipe"); return; }

    pid_t lpid = fork();
    if (lpid == 0) {
        // left child: stdout -> pipe write end
        dup2(fd[1], STDOUT_FILENO);
        close(fd[0]);
        close(fd[1]);
        execvp(largv[0], largv);
        fprintf(stderr, "exec failed: %s\n", largv[0]);
        _exit(127);
    }

    pid_t rpid = fork();
    if (rpid == 0) {
        // right child: stdin <- pipe read end
        dup2(fd[0], STDIN_FILENO);
        close(fd[0]);
        close(fd[1]);
        execvp(rargv[0], rargv);
        fprintf(stderr, "exec failed: %s\n", rargv[0]);
        _exit(127);
    }

    // parent: close BOTH ends, else the right child never sees EOF.
    close(fd[0]);
    close(fd[1]);
    waitpid(lpid, NULL, 0);
    waitpid(rpid, NULL, 0);
}

static void run_line(char *line) {
    char *bar = strchr(line, '|');
    if (bar) {
        *bar = '\0';
        run_pipe(line, bar + 1);
    } else {
        run_simple(line);
    }
}

int main(void) {
    const char *script[] = {
        "echo hi | wc -c",
        "printf a\\nb\\nc\\n | wc -l",
        "ls | wc -l",
    };
    size_t n = sizeof script / sizeof *script;
    for (size_t i = 0; i < n; i++) {
        printf("$ %s -> ", script[i]);
        fflush(stdout);
        char buf[256];
        snprintf(buf, sizeof buf, "%s", script[i]);
        run_line(buf);
    }
    return 0;
}
