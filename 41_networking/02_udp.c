// Module 41 — Demo 2: The SAME echo, but over UDP — connectionless datagrams
//
// TCP gives you a connection: a reliable, ordered byte stream. UDP gives you none of
// that — just independent datagrams (packets) that may be dropped, duplicated, or
// reordered. The API differences are the whole point:
//
//   TCP:  socket -> bind/listen/accept/connect ; then send()/recv() on a connected fd
//   UDP:  socket -> bind                        ; then sendto()/recvfrom() with the
//                                                  peer address on EVERY call
//
// There is no listen(), no accept(), no connect() (you *can* connect() a UDP socket
// for convenience, but it only sets a default peer — no handshake happens).
//
// As in demo 1 we fork() a server + client over 127.0.0.1 on an OS-chosen port, so
// `make run2` is self-contained. Build: make run2.  Read alongside README §6.

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

// Bind a UDP socket to 127.0.0.1 on an OS-chosen port; return fd, report the port.
static int make_udp_socket(uint16_t *out_port) {
    // SOCK_DGRAM = UDP (a datagram socket). No listen()/accept() will follow.
    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) die("socket");

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof addr);
    addr.sin_family = AF_INET;
    addr.sin_port   = htons(0);                    // ephemeral port
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    if (bind(fd, (struct sockaddr *)&addr, sizeof addr) < 0) die("bind");

    struct sockaddr_in bound;
    socklen_t blen = sizeof bound;
    if (getsockname(fd, (struct sockaddr *)&bound, &blen) < 0) die("getsockname");
    *out_port = ntohs(bound.sin_port);
    return fd;
}

// ---- server child: wait for ONE datagram, echo it back to whoever sent it ----
static void run_server(int srv) {
    char buf[256];
    struct sockaddr_in from;          // recvfrom() fills this with the SENDER's address
    socklen_t flen = sizeof from;

    ssize_t n = recvfrom(srv, buf, sizeof buf - 1, 0,
                         (struct sockaddr *)&from, &flen);
    if (n < 0) die("recvfrom");
    buf[n] = '\0';
    printf("[server] got datagram from 127.0.0.1:%u: %s",
           ntohs(from.sin_port), buf);

    // We must say WHERE to send — there is no connection remembering the peer.
    if (sendto(srv, buf, (size_t)n, 0, (struct sockaddr *)&from, flen) < 0)
        die("sendto");
    printf("[server] echoed datagram back\n");
    close(srv);
}

// ---- client (parent): send one datagram to the server, read the reply ----
static void run_client(uint16_t port) {
    int fd = socket(AF_INET, SOCK_DGRAM, 0);   // client need not bind; OS auto-binds on send
    if (fd < 0) die("socket");

    struct sockaddr_in to;
    memset(&to, 0, sizeof to);
    to.sin_family = AF_INET;
    to.sin_port   = htons(port);
    to.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

    const char *msg = "hello over UDP\n";
    if (sendto(fd, msg, strlen(msg), 0, (struct sockaddr *)&to, sizeof to) < 0)
        die("sendto");
    printf("[client] sent datagram: %s", msg);

    char buf[256];
    struct sockaddr_in from;
    socklen_t flen = sizeof from;
    ssize_t n = recvfrom(fd, buf, sizeof buf - 1, 0,
                         (struct sockaddr *)&from, &flen);
    if (n < 0) die("recvfrom");
    buf[n] = '\0';
    printf("[client] got reply:     %s", buf);
    close(fd);
}

int main(void) {
    uint16_t port;
    int srv = make_udp_socket(&port);  // bind in the parent so the port is known
    printf("[main] UDP server on ephemeral port %u\n", port);
    fflush(stdout);  // drain stdout BEFORE fork so the child doesn't inherit & re-emit it

    pid_t pid = fork();
    if (pid < 0) die("fork");

    if (pid == 0) {
        run_server(srv);
        fflush(stdout);  // flush before _exit(): the child skips stdio cleanup
        _exit(0);
    }

    close(srv);
    run_client(port);

    int status;
    waitpid(pid, &status, 0);
    printf("[main] done (note: no handshake ever happened — UDP is connectionless)\n");
    return 0;
}
