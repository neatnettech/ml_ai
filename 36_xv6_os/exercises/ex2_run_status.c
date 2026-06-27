// Exercise 36.2 — Run a command and return its exit status  (native; make ex2)
//
// Implement run_status(): fork(), have the child exec the given argv, the parent
// waitpid() for it, and RETURN the child's exit code (0 = success). This is the
// reusable core of demos 1 and 4 — and what xv6's `wait(0)` gives the shell so it
// can report `$?`.
//
// Verify on the two canonical probes the system ships for exactly this purpose:
//   /usr/bin/true   exits 0
//   /usr/bin/false  exits 1
//
// Check against solutions/ex2_run_status.c with `make sol2`. Expected (make sol2):
//   run_status(/usr/bin/true ) = 0
//   run_status(/usr/bin/false) = 1
//   run_status(/bin/echo ok  ) = 0   (and prints: ok)

#define _DARWIN_C_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>

// Run argv[] (argv[0] is the program, NULL-terminated). Return its exit status,
// or -1 if it did not exit normally / could not be started.
static int run_status(char *argv[]) {
    // TODO:
    //  1. pid_t pid = fork();
    //  2. child (pid == 0): execvp(argv[0], argv); on failure _exit(127);
    //  3. parent: int st; waitpid(pid, &st, 0);
    //     return WIFEXITED(st) ? WEXITSTATUS(st) : -1;
    (void)argv;
    return -1;  // replace with the real implementation
}

int main(void) {
    char *t[]  = {"/usr/bin/true",  NULL};
    char *f[]  = {"/usr/bin/false", NULL};
    char *e[]  = {"/bin/echo", "ok", NULL};

    printf("run_status(/usr/bin/true ) = %d\n", run_status(t));
    printf("run_status(/usr/bin/false) = %d\n", run_status(f));
    printf("run_status(/bin/echo ok  ) = %d\n", run_status(e));
    return 0;
}
