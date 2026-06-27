// Exercise 42.2 — Lamport clock update rules
//
// Implement the two Lamport-clock update rules from Demo 2, then use them to order a
// scripted event set across two nodes. Match the expected output in README.md §5.
// Solution in ../solutions/ex2_lamport_update.c.
//
//   on a local or SEND event:  clock = clock + 1   (and the send attaches its clock)
//   on a RECEIVE event:        clock = max(clock, incoming) + 1

#include <stdio.h>

// Advance the clock for a local/internal/send event. Return the new value.
int lamport_tick(int clock) {
    // TODO: increment and return the clock.
    (void)clock;
    return 0;
}

// Update the clock on receiving a message stamped `incoming`. Return the new value.
int lamport_recv(int clock, int incoming) {
    // TODO: clock = max(clock, incoming) + 1; return it.
    (void)clock; (void)incoming;
    return 0;
}

int main(void) {
    // P0 and P1. Script:
    //   a: P0 local
    //   b: P0 send m ->P1   (m carries P0's clock)
    //   c: P1 local
    //   d: P1 recv m
    int p0 = 0, p1 = 0, m;
    int la, lb, lc, ld;

    p0 = lamport_tick(p0);         la = p0; printf("a  P0 local       L0=%d\n", p0);
    p0 = lamport_tick(p0); m = p0; lb = p0; printf("b  P0 send m      L0=%d (m=%d)\n", p0, m);
    p1 = lamport_tick(p1);         lc = p1; printf("c  P1 local       L1=%d\n", p1);
    p1 = lamport_recv(p1, m);      ld = p1; printf("d  P1 recv m      L1=%d\n", p1);

    printf("\nordering by Lamport timestamp: a(%d) < b(%d), c(%d) < d(%d)\n", la, lb, lc, ld);
    printf("causal edge b -> d holds: L(b)=%d < L(d)=%d\n", lb, ld);
    return 0;
}
