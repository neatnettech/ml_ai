// Module 42 — Demo 2: Lamport & vector clocks (logical time)
//
// Physical clocks on different machines drift and can't be perfectly synced, so you
// cannot trust wall-clock timestamps to order events across nodes. Lamport's insight
// (1978): you don't need real time — you need a counter that respects causality, i.e.
// "happens-before". This demo runs a fixed event sequence across 3 nodes and shows:
//   - the Lamport rule (a single integer) gives a total order consistent with causality
//   - vector clocks additionally let you DETECT concurrency (neither event caused the other)
//
// Fully deterministic: the event script is hard-coded. Build & run: make run2
//
// Read top to bottom alongside README.md §2.

#include <stdio.h>

#define N 3   // three nodes: 0, 1, 2

// ---- Lamport clock rules --------------------------------------------------------
//   local/internal event:  L = L + 1
//   send:                   L = L + 1;  attach L to the message
//   receive(msg):           L = max(L, msg.L) + 1
// Guarantee: if event a happens-before event b, then L(a) < L(b). (Not the converse.)

// ---- Vector clock rules ---------------------------------------------------------
//   each node i keeps V[N]; on any local event V[i] += 1
//   send: V[i] += 1; attach the whole vector
//   receive(msg): V[k] = max(V[k], msg.V[k]) for all k; then V[i] += 1
// Compare(a,b): a -> b iff a<=b elementwise and a!=b; incomparable => CONCURRENT.

static void vc_print(const int v[N]) {
    printf("[%d,%d,%d]", v[0], v[1], v[2]);
}

int main(void) {
    // A scripted causal chain across 3 nodes (P0, P1, P2):
    //   e1: P0 local
    //   e2: P0 SENDS m1 to P1
    //   e3: P1 RECEIVES m1
    //   e4: P1 SENDS m2 to P2
    //   e5: P2 RECEIVES m2
    //   e6: P2 local
    // Plus a CONCURRENT event x1: P2 does a local op that does NOT depend on m2.
    printf("=== Lamport logical clocks across 3 nodes ===\n");
    int L[N] = {0, 0, 0};

    int m1, m2;  // timestamps carried on the two messages

    L[0]++; printf("  e1  P0 local            L0=%d\n", L[0]);
    L[0]++; m1 = L[0]; printf("  e2  P0 send m1 ->P1     L0=%d (m1 carries %d)\n", L[0], m1);
    L[1] = (L[1] > m1 ? L[1] : m1) + 1;
            printf("  e3  P1 recv m1          L1=max(%d,%d)+1=%d\n", 0, m1, L[1]);
    L[1]++; m2 = L[1]; printf("  e4  P1 send m2 ->P2     L1=%d (m2 carries %d)\n", L[1], m2);
    L[2] = (L[2] > m2 ? L[2] : m2) + 1;
            printf("  e5  P2 recv m2          L2=max(%d,%d)+1=%d\n", 0, m2, L[2]);
    L[2]++; printf("  e6  P2 local            L2=%d\n", L[2]);

    printf("\n  Lamport timestamps respect causality: e1<e2<e3<e4<e5<e6 (1<2<3<4<5<6).\n");
    printf("  A wall clock could not promise this: P1's clock might read EARLIER than\n");
    printf("  P0's even though e3 causally FOLLOWS e2. Logical time fixes that.\n");

    // ---- Now vector clocks, to DETECT concurrency the scalar can't see ----------
    printf("\n=== Vector clocks: detecting concurrency ===\n");
    int V[N][N] = {{0,0,0},{0,0,0},{0,0,0}};
    int msg[N];  // a message's attached vector

    V[0][0]++;                                   // e2 again, but vector form: P0 sends
    for (int k = 0; k < N; k++) msg[k] = V[0][k];
    printf("  P0 send m1   V0="); vc_print(V[0]); printf("\n");

    for (int k = 0; k < N; k++) if (msg[k] > V[1][k]) V[1][k] = msg[k];
    V[1][1]++;                                    // e3: P1 receives m1
    printf("  P1 recv m1   V1="); vc_print(V[1]); printf("\n");

    // Snapshot the event "P1 received m1" for later comparison.
    int eventA[N]; for (int k = 0; k < N; k++) eventA[k] = V[1][k];

    // A CONCURRENT event on P2 that never saw m1/m2:
    V[2][2]++;                                    // x1: P2 local, independent
    int eventB[N]; for (int k = 0; k < N; k++) eventB[k] = V[2][k];
    printf("  P2 local x1  V2="); vc_print(V[2]); printf("\n");

    // Compare eventA (P1 recv m1) and eventB (P2 local x1).
    int a_le_b = 1, b_le_a = 1, equal = 1;
    for (int k = 0; k < N; k++) {
        if (eventA[k] > eventB[k]) a_le_b = 0;
        if (eventB[k] > eventA[k]) b_le_a = 0;
        if (eventA[k] != eventB[k]) equal = 0;
    }
    printf("\n  compare A="); vc_print(eventA);
    printf(" (P1 recv m1)  vs  B="); vc_print(eventB); printf(" (P2 local x1):\n");
    if (equal)            printf("  -> same event\n");
    else if (a_le_b)      printf("  -> A happens-before B\n");
    else if (b_le_a)      printf("  -> B happens-before A\n");
    else                  printf("  -> CONCURRENT: neither caused the other (a scalar\n"
                                 "     Lamport clock would hide this, only a vector shows it)\n");
    return 0;
}
