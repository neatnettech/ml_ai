// SOLUTION 36.2 — Run a command and return its exit status  (native; make sol2)

#define _DARWIN_C_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>

static int run_status(char *argv[]) {
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return -1;
    }
    if (pid == 0) {
        execvp(argv[0], argv);
        _exit(127);                 // only reached if the program could not start
    }
    int st = 0;
    if (waitpid(pid, &st, 0) < 0) return -1;
    return WIFEXITED(st) ? WEXITSTATUS(st) : -1;
}

int main(void) {
    char *t[] = {"/usr/bin/true",  NULL};
    char *f[] = {"/usr/bin/false", NULL};
    char *e[] = {"/bin/echo", "ok", NULL};

    printf("run_status(/usr/bin/true ) = %d\n", run_status(t));
    printf("run_status(/usr/bin/false) = %d\n", run_status(f));
    printf("run_status(/bin/echo ok  ) = %d\n", run_status(e));
    return 0;
}
