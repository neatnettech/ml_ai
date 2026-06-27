// Exercise 41.3 — Serve several sequential clients with an accept-loop
//
// Demo 1's server accepts exactly ONE client then quits. A real server loops:
// accept -> handle -> close -> accept again. Your job: implement `run_server()` so it
// accepts and echoes for NCLIENTS clients in a row (sequentially, one at a time).
//
// The clients are forked for you and each prints the echo it got back, so you can
// verify every client was served. Fill in the TODOs; `make ex3` should match
// `make sol3`. Solution in ../solutions/ex3_accept_loop.c.

#define _DARWIN_C_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/wait.h>

#define NCLIENTS 3

static void die(const char *msg) { perror(msg); exit(1); }

// ===================== YOUR CODE: the accept-loop =====================
// Accept and echo for `n_clients` connections, ONE at a time, then close `srv`.
static void run_server(int srv, int n_clients) {
    // TODO: loop n_clients times. Each iteration:
    //   1. int conn = accept(srv, NULL, NULL);  (check for < 0)
    //   2. recv() one chunk into a buffer
    //   3. send() those exact bytes back (echo)
    //   4. close(conn)
    // After the loop, close(srv).
    (void)srv; (void)n_clients;  // remove once implemented
}
// =====================================================================

// --- provided client (forked): connect, send a numbered line, print echo ---
static void run_client(uint16_t port, int id) {
    // Safety net: until run_server() is implemented nobody echoes, so recv() would
    // block forever. A 5s alarm makes the client exit so `make ex3` never hangs.
    alarm(5);
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) die("socket");
    struct sockaddr_in addr; memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET; addr.sin_port = htons(port);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (connect(sock, (struct sockaddr *)&addr, sizeof addr) < 0) die("connect");
    char msg[64]; snprintf(msg, sizeof msg, "ping from client %d\n", id);
    send(sock, msg, strlen(msg), 0);
    char buf[128]; ssize_t n = recv(sock, buf, sizeof buf - 1, 0);
    if (n > 0) { buf[n] = '\0'; printf("[client %d] echo: %s", id, buf); }
    fflush(stdout);   // flush before _exit(): the forked child skips stdio cleanup
    close(sock);
}

static uint16_t bind_listen(int *out_srv) {
    int srv = socket(AF_INET, SOCK_STREAM, 0);
    if (srv < 0) die("socket");
    int yes = 1; setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof yes);
    struct sockaddr_in a; memset(&a, 0, sizeof a);
    a.sin_family = AF_INET; a.sin_port = htons(0); a.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(srv, (struct sockaddr *)&a, sizeof a) < 0) die("bind");
    if (listen(srv, 8) < 0) die("listen");
    struct sockaddr_in b; socklen_t bl = sizeof b;
    getsockname(srv, (struct sockaddr *)&b, &bl);
    *out_srv = srv;
    return ntohs(b.sin_port);
}

int main(void) {
    int srv; uint16_t port = bind_listen(&srv);
    printf("[main] echo server (accept-loop) on port %u, %d clients\n", port, NCLIENTS);
    fflush(stdout);  // drain stdout BEFORE fork so children don't re-emit the buffer

    pid_t pid = fork();
    if (pid < 0) die("fork");
    if (pid == 0) { run_server(srv, NCLIENTS); _exit(0); }

    close(srv);
    // Fork the clients sequentially: wait for each before starting the next, so the
    // single-threaded accept-loop serves them one after another in order.
    for (int i = 0; i < NCLIENTS; i++) {
        pid_t c = fork();
        if (c < 0) die("fork");
        if (c == 0) { run_client(port, i); _exit(0); }
        waitpid(c, NULL, 0);
    }
    waitpid(pid, NULL, 0);
    printf("[main] all %d clients served, done\n", NCLIENTS);
    return 0;
}
