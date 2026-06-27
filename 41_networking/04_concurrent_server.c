// Module 41 — Demo 4: A concurrent server (thread-per-connection)
//
// A single accept/recv/send loop serves ONE client at a time — the next client waits.
// Real servers handle many clients at once. Two classic models:
//
//   fork-per-connection:   accept(), fork() a child to handle the client (simple,
//                          heavier; each child has its own address space)
//   thread-per-connection: accept(), spawn a pthread to handle the client (lighter,
//                          shared memory; what FastAPI/uvicorn workers resemble)
//
// We use threads here (-pthread). The server runs in a background thread; it accepts a
// BOUNDED number of clients (so the program terminates on its own), handing each to a
// worker thread. The main thread forks a few CLIENTS that connect concurrently. Each
// reply carries the worker's id so you can SEE that different clients are served by
// different threads. Build: make run4.  Read alongside README §8.

#define _DARWIN_C_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/wait.h>

#define NCLIENTS 3   // how many clients connect (server accepts exactly this many)

static void die(const char *msg) { perror(msg); exit(1); }

// --- per-connection worker: read one line, reply with worker id, close ---
static void *worker(void *arg) {
    int conn = (int)(long)arg;
    char buf[256];
    ssize_t n = recv(conn, buf, sizeof buf - 1, 0);
    if (n > 0) {
        buf[n] = '\0';
        char reply[320];
        // thread id (just the low bits) proves a distinct thread handled this client
        snprintf(reply, sizeof reply, "thread %lu handled: %s",
                 (unsigned long)(pthread_self()) & 0xffff, buf);
        send(conn, reply, strlen(reply), 0);
    }
    close(conn);
    return NULL;
}

// --- server thread: accept exactly NCLIENTS connections, one worker thread each ---
static void *server_thread(void *arg) {
    int srv = (int)(long)arg;
    pthread_t workers[NCLIENTS];
    for (int i = 0; i < NCLIENTS; i++) {
        int conn = accept(srv, NULL, NULL);
        if (conn < 0) die("accept");
        // pass the connection fd to a new worker thread (cast through long, no malloc)
        pthread_create(&workers[i], NULL, worker, (void *)(long)conn);
    }
    for (int i = 0; i < NCLIENTS; i++) pthread_join(workers[i], NULL);
    close(srv);
    return NULL;
}

// --- one client (runs in a forked child): connect, send, print reply ---
static void run_client(uint16_t port, int id) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) die("socket");
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_port   = htons(port);
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (connect(sock, (struct sockaddr *)&addr, sizeof addr) < 0) die("connect");

    char msg[64];
    snprintf(msg, sizeof msg, "hi from client %d\n", id);
    send(sock, msg, strlen(msg), 0);

    char buf[320];
    ssize_t n = recv(sock, buf, sizeof buf - 1, 0);
    if (n > 0) { buf[n] = '\0'; printf("[client %d] reply: %s", id, buf); }
    fflush(stdout);   // flush before _exit(): the child skips stdio cleanup otherwise
    close(sock);
}

int main(void) {
    // Bind+listen in the parent so the port exists before any client connects.
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
    if (listen(srv, 16) < 0) die("listen");
    struct sockaddr_in bound;
    socklen_t blen = sizeof bound;
    getsockname(srv, (struct sockaddr *)&bound, &blen);
    uint16_t port = ntohs(bound.sin_port);
    printf("[main] concurrent server on ephemeral port %u, expecting %d clients\n",
           port, NCLIENTS);

    // Run the accept-loop in a background thread so main can also fork clients.
    pthread_t srv_tid;
    pthread_create(&srv_tid, NULL, server_thread, (void *)(long)srv);

    fflush(stdout);  // drain stdout BEFORE forking so children don't re-emit the buffer

    // Fork NCLIENTS children that all connect at once -> they're served concurrently.
    pid_t kids[NCLIENTS];
    for (int i = 0; i < NCLIENTS; i++) {
        pid_t pid = fork();
        if (pid < 0) die("fork");
        if (pid == 0) { run_client(port, i); _exit(0); }
        kids[i] = pid;
    }

    // Reap every client child, then join the server thread — clean, no hang.
    for (int i = 0; i < NCLIENTS; i++) waitpid(kids[i], NULL, 0);
    pthread_join(srv_tid, NULL);
    printf("[main] all %d clients served concurrently, done\n", NCLIENTS);
    return 0;
}
