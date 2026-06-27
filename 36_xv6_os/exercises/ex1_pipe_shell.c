// Exercise 36.1 — Add a single `|` pipe to the tiny shell  (native; make ex1)
//
// Goal: given a command line that may contain ONE pipe, e.g.  "ls | wc -l", run the
// left command with its stdout connected to the right command's stdin — exactly what
// xv6's user/sh.c does for a `|` node, and the mechanism shown in 02_pipes.c.
//
// We give you the parsing/splitting and the no-pipe path. You implement run_pipe():
//   pipe() -> fork left (stdout = pipe write end) -> fork right (stdin = pipe read end)
//   -> close both ends in the parent -> wait for both.
//
// Check against solutions/ex1_pipe_shell.c with `make sol1`. Expected (make sol1):
//   $ echo hi | wc -c        -> 3        (2 chars + newline)
//   $ printf 'a\nb\nc\n' | wc -l -> 3
//   $ ls | wc -l             -> (a number > 0; counts entries in this dir)

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

// Run a single command (no pipe) and wait for it.
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

// Run  left | right.  `left` and `right` are NUL-terminated command strings.
static void run_pipe(char *left, char *right) {
    // TODO: implement the pipeline.
    //  1. char *largv[MAXARGS], *rargv[MAXARGS]; tokenize(left, largv, ...);
    //     tokenize(right, rargv, ...);
    //  2. int fd[2]; pipe(fd);
    //  3. fork the LEFT child:  dup2(fd[1], STDOUT_FILENO); close fd[0],fd[1]; execvp(largv...)
    //  4. fork the RIGHT child: dup2(fd[0], STDIN_FILENO);  close fd[0],fd[1]; execvp(rargv...)
    //  5. parent: close(fd[0]); close(fd[1]); waitpid both children.
    //  Remember: the parent MUST close both pipe ends or the reader never sees EOF.
    (void)left; (void)right;
    fprintf(stderr, "run_pipe: not implemented yet (see TODO)\n");
}

// Run one line: if it contains '|', split once and call run_pipe; else run_simple.
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
    // A canned, terminating set of pipelines so the build is verifiable.
    const char *script[] = {
        "echo hi | wc -c",
        "printf a\\nb\\nc\\n | wc -l",   // note: printf gets the literal backslashes;
                                          // run_pipe should still wire the pipe up.
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
