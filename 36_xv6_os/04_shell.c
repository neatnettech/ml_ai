// Module 36 — Demo 4: a tiny shell — the condensed structure of xv6's user/sh.c
//
// A shell is a loop:  print a prompt -> read a line -> parse it -> fork() a child ->
// the child runs the program with execvp() -> the parent wait()s. That is the whole
// job. Strip away xv6's pipes/redirection/backgrounding and what remains is this file.
//
// Running it:
//   make run4        — DEMO MODE: feeds a fixed list of commands so it's verifiable
//                      and terminates on its own (no human at the keyboard).
//   ./bin/04_shell   — INTERACTIVE: type commands, Ctrl-D (EOF) to quit.
//   echo "ls" | ./bin/04_shell   — pipe commands in on stdin.
//
// Read alongside README.md PART A §4.  (Exercise 36.1 extends this with a `|` pipe.)

#define _DARWIN_C_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>

#define MAXARGS 32

// Split `line` in place into argv tokens on spaces/tabs/newlines. Returns argc.
static int tokenize(char *line, char *argv[], int max) {
    int argc = 0;
    char *p = line;
    while (argc < max - 1) {
        while (*p == ' ' || *p == '\t' || *p == '\n') *p++ = '\0';  // skip blanks
        if (*p == '\0') break;
        argv[argc++] = p;                                            // start of a token
        while (*p && *p != ' ' && *p != '\t' && *p != '\n') p++;    // to end of token
    }
    argv[argc] = NULL;
    return argc;
}

// fork + run + wait for one command line. Returns the child's exit status.
static int run_line(char *line) {
    char *argv[MAXARGS];
    int argc = tokenize(line, argv, MAXARGS);
    if (argc == 0) return 0;                  // blank line: nothing to do

    if (strcmp(argv[0], "exit") == 0) {       // a builtin must run in THIS process,
        exit(0);                              // not a child — same as xv6's `cd`.
    }

    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return -1; }

    if (pid == 0) {
        execvp(argv[0], argv);                // replace child image with the program
        fprintf(stderr, "tinysh: command not found: %s\n", argv[0]);
        _exit(127);
    }

    int status = 0;
    waitpid(pid, &status, 0);                  // parent reaps the child
    return WIFEXITED(status) ? WEXITSTATUS(status) : -1;
}

// Read lines from `in`, running each one, until EOF. (`prompt` controls the prompt.)
static void shell_loop(FILE *in, int prompt) {
    char line[256];
    for (;;) {
        if (prompt) { printf("tinysh$ "); fflush(stdout); }
        if (fgets(line, sizeof line, in) == NULL) break;   // EOF -> clean exit
        run_line(line);
    }
}

int main(int argc, char *argv[]) {
    // DEMO MODE: `--demo` (or `make run4`) runs a canned, terminating command list so
    // the build is verifiable without an interactive terminal.
    if (argc > 1 && strcmp(argv[1], "--demo") == 0) {
        const char *script[] = {
            "echo hello from tinysh",
            "echo the next line lists this directory:",
            "ls",
            "nope_not_a_real_command",   // shows the not-found path
        };
        size_t n = sizeof script / sizeof *script;
        for (size_t i = 0; i < n; i++) {
            printf("tinysh$ %s\n", script[i]);
            char buf[256];
            snprintf(buf, sizeof buf, "%s", script[i]);
            run_line(buf);
        }
        printf("tinysh$ exit\n");        // the builtin that ends an interactive session
        return 0;
    }

    // INTERACTIVE / PIPED MODE: prompt only when stdin is a real terminal.
    shell_loop(stdin, isatty(STDIN_FILENO));
    return 0;
}
