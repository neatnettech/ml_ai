// Module 41 — Demo 3: A tiny line-based request/response protocol (an RPC)
//
// Raw send()/recv() move BYTES; an application needs a PROTOCOL — an agreed message
// format — on top. Here we define a minimal text protocol over TCP, the same shape
// HTTP and Redis use:
//
//   request:   one '\n'-terminated line, "VERB args..."
//   response:  one '\n'-terminated line
//
//   SET key value   -> OK
//   GET key         -> VALUE <v>   |   NOTFOUND
//   ADD a b         -> RESULT <a+b>            (a tiny remote procedure call)
//   PING            -> PONG
//   anything else   -> ERR unknown command
//
// The server parses each line and dispatches; the client sends a script of requests.
// "Framing" = knowing where one message ends; here the frame delimiter is '\n'. As in
// the other demos we fork() over loopback on an ephemeral port. Build: make run3.
// Read alongside README §7.

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

// --- a toy single-key store so GET/SET have something to talk to ---
static char kv_key[64]   = {0};
static char kv_value[64] = {0};
static int  kv_set       = 0;

// Parse ONE request line and write the response line into `out`.
static void handle_request(const char *line, char *out, size_t outsz) {
    char verb[16] = {0}, a[64] = {0}, b[64] = {0};
    int parts = sscanf(line, "%15s %63s %63s", verb, a, b);

    if (parts >= 1 && strcmp(verb, "PING") == 0) {
        snprintf(out, outsz, "PONG\n");
    } else if (parts >= 3 && strcmp(verb, "SET") == 0) {
        snprintf(kv_key,   sizeof kv_key,   "%s", a);
        snprintf(kv_value, sizeof kv_value, "%s", b);
        kv_set = 1;
        snprintf(out, outsz, "OK\n");
    } else if (parts >= 2 && strcmp(verb, "GET") == 0) {
        if (kv_set && strcmp(kv_key, a) == 0)
            snprintf(out, outsz, "VALUE %s\n", kv_value);
        else
            snprintf(out, outsz, "NOTFOUND\n");
    } else if (parts >= 3 && strcmp(verb, "ADD") == 0) {
        long x = strtol(a, NULL, 10), y = strtol(b, NULL, 10);
        snprintf(out, outsz, "RESULT %ld\n", x + y);  // the actual "remote procedure"
    } else {
        snprintf(out, outsz, "ERR unknown command\n");
    }
}

// --- server child: read requests line-by-line until the client closes ---
static void run_server(int srv) {
    struct sockaddr_in cli;
    socklen_t clen = sizeof cli;
    int conn = accept(srv, (struct sockaddr *)&cli, &clen);
    if (conn < 0) die("accept");

    // recv() does not respect message boundaries, so we buffer and split on '\n'.
    char buf[1024];
    size_t used = 0;
    for (;;) {
        ssize_t n = recv(conn, buf + used, sizeof buf - used - 1, 0);
        if (n <= 0) break;           // 0 = peer closed; <0 = error -> stop
        used += (size_t)n;
        buf[used] = '\0';

        char *start = buf, *nl;
        while ((nl = strchr(start, '\n')) != NULL) {
            *nl = '\0';              // terminate this one line (drops the '\n')
            char resp[128];
            handle_request(start, resp, sizeof resp);
            printf("[server] %-15s -> %s", start, resp);  // start has no newline now
            send(conn, resp, strlen(resp), 0);
            start = nl + 1;
        }
        // Slide any partial (unterminated) line to the front of the buffer.
        used = strlen(start);
        memmove(buf, start, used + 1);
    }
    close(conn);
    close(srv);
}

// Send one request line, print the single-line response.
static void request(int sock, const char *line) {
    send(sock, line, strlen(line), 0);
    char buf[128];
    ssize_t n = recv(sock, buf, sizeof buf - 1, 0);
    if (n <= 0) return;
    buf[n] = '\0';
    // strip the request's trailing newline so it sits in one tidy column
    char clean[64];
    snprintf(clean, sizeof clean, "%s", line);
    char *nl = strchr(clean, '\n'); if (nl) *nl = '\0';
    printf("[client] %-15s <- %s", clean, buf);
}

// --- client (parent): run a fixed script of requests ---
static void run_client(uint16_t port) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) die("socket");

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_port   = htons(port);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (connect(sock, (struct sockaddr *)&addr, sizeof addr) < 0) die("connect");

    request(sock, "PING\n");
    request(sock, "GET color\n");
    request(sock, "SET color blue\n");
    request(sock, "GET color\n");
    request(sock, "ADD 19 23\n");
    request(sock, "BOGUS x\n");

    close(sock);  // closing flushes the server's recv() loop (it sees EOF)
}

int main(void) {
    // Bind+listen inline (kept small; demo 1 shows the helper version).
    int srv = socket(AF_INET, SOCK_STREAM, 0);
    if (srv < 0) die("socket");
    int yes = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof yes);
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_port   = htons(0);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(srv, (struct sockaddr *)&addr, sizeof addr) < 0) die("bind");
    if (listen(srv, 8) < 0) die("listen");
    struct sockaddr_in bound;
    socklen_t blen = sizeof bound;
    getsockname(srv, (struct sockaddr *)&bound, &blen);
    uint16_t port = ntohs(bound.sin_port);
    printf("[main] protocol server on ephemeral port %u\n", port);
    fflush(stdout);  // drain stdout BEFORE fork so the child doesn't inherit & re-emit it

    pid_t pid = fork();
    if (pid < 0) die("fork");
    if (pid == 0) { run_server(srv); fflush(stdout); _exit(0); }

    close(srv);
    run_client(port);

    int status;
    waitpid(pid, &status, 0);
    printf("[main] done\n");
    return 0;
}
