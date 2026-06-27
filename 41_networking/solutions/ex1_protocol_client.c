// SOLUTION 41.1 — Client side of the line protocol

#define _DARWIN_C_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/wait.h>

static void die(const char *msg) { perror(msg); exit(1); }

static void send_request(uint16_t port, const char *line) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) die("socket");

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_port   = htons(port);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (connect(sock, (struct sockaddr *)&addr, sizeof addr) < 0) die("connect");

    if (send(sock, line, strlen(line), 0) < 0) die("send");

    char buf[256];
    ssize_t n = recv(sock, buf, sizeof buf - 1, 0);
    if (n < 0) die("recv");
    buf[n] = '\0';

    // strip the trailing newline of the request just for tidy printing
    char clean[128];
    snprintf(clean, sizeof clean, "%s", line);
    char *nl = strchr(clean, '\n'); if (nl) *nl = '\0';
    printf("[client] %-14s -> %s", clean, buf);

    close(sock);
}

// --- provided server (one request per short-lived connection) ---
static void handle(const char *line, char *out, size_t outsz) {
    char verb[16] = {0}, a[64] = {0}, b[64] = {0};
    int parts = sscanf(line, "%15s %63s %63s", verb, a, b);
    static char k[64], v[64]; static int isset = 0;
    if (parts >= 1 && !strcmp(verb, "PING"))                 snprintf(out, outsz, "PONG\n");
    else if (parts >= 3 && !strcmp(verb, "SET")) { snprintf(k,sizeof k,"%s",a); snprintf(v,sizeof v,"%s",b); isset=1; snprintf(out, outsz, "OK\n"); }
    else if (parts >= 2 && !strcmp(verb, "GET"))  snprintf(out, outsz, (isset && !strcmp(k,a)) ? "VALUE %s\n" : "NOTFOUND\n", v);
    else if (parts >= 3 && !strcmp(verb, "ADD"))  snprintf(out, outsz, "RESULT %ld\n", strtol(a,0,10)+strtol(b,0,10));
    else                                          snprintf(out, outsz, "ERR unknown command\n");
}

static void run_server(int srv, int n_requests) {
    for (int i = 0; i < n_requests; i++) {
        int conn = accept(srv, NULL, NULL);
        if (conn < 0) die("accept");
        char buf[256];
        ssize_t got = recv(conn, buf, sizeof buf - 1, 0);
        if (got > 0) {
            buf[got] = '\0';
            char *nl = strchr(buf, '\n'); if (nl) *nl = '\0';
            char resp[128]; handle(buf, resp, sizeof resp);
            send(conn, resp, strlen(resp), 0);
        }
        close(conn);
    }
    close(srv);
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
    const char *script[] = { "PING\n", "SET color blue\n", "GET color\n", "ADD 19 23\n" };
    int n = (int)(sizeof script / sizeof *script);

    int srv; uint16_t port = bind_listen(&srv);
    pid_t pid = fork();
    if (pid < 0) die("fork");
    if (pid == 0) { run_server(srv, n); _exit(0); }

    close(srv);
    for (int i = 0; i < n; i++) send_request(port, script[i]);

    waitpid(pid, NULL, 0);
    return 0;
}
