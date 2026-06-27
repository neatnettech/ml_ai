// Module 41 — Demo 1: A TCP echo client + server in ONE program
//
// This is the smallest complete picture of the BSD sockets API. We fork() so the
// SAME program plays both roles over the loopback interface (127.0.0.1):
//
//   server child:  socket -> bind(port 0) -> listen -> accept -> recv -> send -> close
//   client parent: socket -> connect      -> send -> recv -> close
//
// Binding to port 0 asks the OS for any free EPHEMERAL port; we read it back with
// getsockname() and hand it to the client. So `make run1` works with no external
// network, no second terminal, and no fixed port to collide with. Build: make run1
//
// Read top to bottom alongside README.md §1–§3.

#define _DARWIN_C_SOURCE  // expose POSIX/BSD socket extras on macOS under -std=c11

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>       // fork, close, read, write
#include <sys/socket.h>   // socket, bind, listen, accept, connect, send, recv
#include <netinet/in.h>   // struct sockaddr_in, htons, INADDR_LOOPBACK
#include <arpa/inet.h>    // htonl
#include <sys/wait.h>     // waitpid

static void die(const char *msg) { perror(msg); exit(1); }

// Create a listening TCP socket bound to 127.0.0.1 on an OS-chosen port.
// Writes the chosen port (host byte order) into *out_port and returns the fd.
static int make_listener(uint16_t *out_port) {
    // AF_INET = IPv4, SOCK_STREAM = TCP (a reliable, ordered byte stream).
    int srv = socket(AF_INET, SOCK_STREAM, 0);
    if (srv < 0) die("socket");

    // Let us re-bind the address immediately after a previous run (TIME_WAIT).
    int yes = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof yes);

    // struct sockaddr_in describes an IPv4 endpoint: family + port + IP address.
    // EVERYTHING that goes on the wire is in NETWORK byte order (big-endian), so we
    // convert with htons (16-bit port) and htonl (32-bit address). See README §4.
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_port   = htons(0);                    // port 0 => OS picks an ephemeral port
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK); // 127.0.0.1, never leaves this machine

    if (bind(srv, (struct sockaddr *)&addr, sizeof addr) < 0) die("bind");
    if (listen(srv, 8) < 0) die("listen");         // backlog of pending connections

    // Ask the kernel which port it actually assigned.
    struct sockaddr_in bound;
    socklen_t blen = sizeof bound;
    if (getsockname(srv, (struct sockaddr *)&bound, &blen) < 0) die("getsockname");
    *out_port = ntohs(bound.sin_port);             // network -> host byte order

    return srv;
}

// ---- server child: accept ONE client, echo ONE line, then exit ----
static void run_server(int srv) {
    struct sockaddr_in cli;
    socklen_t clen = sizeof cli;
    int conn = accept(srv, (struct sockaddr *)&cli, &clen);  // blocks until a client connects
    if (conn < 0) die("accept");
    printf("[server] accepted a client\n");

    char buf[256];
    ssize_t n = recv(conn, buf, sizeof buf - 1, 0);  // blocks until bytes arrive
    if (n < 0) die("recv");
    buf[n] = '\0';
    printf("[server] received: %s", buf);

    if (send(conn, buf, (size_t)n, 0) < 0) die("send");  // echo the exact bytes back
    printf("[server] echoed it back\n");

    close(conn);
    close(srv);
}

// ---- client (parent): connect, send a line, read the echo ----
static void run_client(uint16_t port) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) die("socket");

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_port   = htons(port);                 // same port the server bound
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    // connect() performs the TCP 3-way handshake (SYN / SYN-ACK / ACK) — README §5.
    if (connect(sock, (struct sockaddr *)&addr, sizeof addr) < 0) die("connect");
    printf("[client] connected to 127.0.0.1:%u\n", port);

    const char *msg = "hello over TCP\n";
    if (send(sock, msg, strlen(msg), 0) < 0) die("send");
    printf("[client] sent:     %s", msg);

    char buf[256];
    ssize_t n = recv(sock, buf, sizeof buf - 1, 0);
    if (n < 0) die("recv");
    buf[n] = '\0';
    printf("[client] got back: %s", buf);

    close(sock);
}

int main(void) {
    uint16_t port;
    int srv = make_listener(&port);  // bind+listen in the PARENT so the port exists
    printf("[main] listening on ephemeral port %u\n", port);
    fflush(stdout);  // drain stdout BEFORE fork so the child doesn't inherit & re-emit it

    pid_t pid = fork();
    if (pid < 0) die("fork");

    if (pid == 0) {
        // Child = server. It already inherited the listening fd.
        run_server(srv);
        fflush(stdout);  // flush before _exit(): the child skips stdio cleanup
        _exit(0);
    }

    // Parent = client. Close our copy of the listening fd; we only need to connect.
    close(srv);
    run_client(port);

    // Always reap the child so we exit cleanly with no zombies and no hang.
    int status;
    waitpid(pid, &status, 0);
    printf("[main] server child exited, done\n");
    return 0;
}
