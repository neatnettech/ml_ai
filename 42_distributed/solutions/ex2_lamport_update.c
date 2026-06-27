// SOLUTION 42.2 — Lamport clock update rules

#include <stdio.h>

int lamport_tick(int clock) {
    return clock + 1;
}

int lamport_recv(int clock, int incoming) {
    int hi = clock > incoming ? clock : incoming;
    return hi + 1;
}

int main(void) {
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
