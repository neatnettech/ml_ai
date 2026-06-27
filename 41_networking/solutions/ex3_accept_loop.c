// SOLUTION 41.3 — Serve several sequential clients with an accept-loop

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

static void run_server(int srv, int n_clients) {
    for (int i = 0; i < n_clients; i++) {
        int conn = accept(srv, NULL, NULL);   // wait for the next client
        if (conn < 0) die("accept");
        char buf[256];
        ssize_t n = recv(conn, buf, sizeof buf - 1, 0);
        if (n > 0) send(conn, buf, (size_t)n, 0);  // echo the exact bytes back
        close(conn);                          // done with this client; loop again
    }
    close(srv);
}

static void run_client(uint16_t port, int id) {
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
