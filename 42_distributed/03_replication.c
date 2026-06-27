// Module 42 — Demo 3: Primary/backup replication, stale reads, and quorums
//
// To survive a node crash you keep COPIES of the data on several nodes. The simplest
// scheme is primary/backup: all writes go to a primary, which forwards them to backups.
// But replication takes time, so a read served by a lagging backup can be STALE —
// it returns an old value. The fix used by Dynamo/Cassandra-style systems is QUORUMS:
// require a write to reach W nodes and a read to consult R nodes, with R + W > N. Then
// every read quorum overlaps every write quorum, so a read always SEES the latest write.
//
// We model N=3 replicas as an array. Fully deterministic. Build & run: make run3
//
// Read top to bottom alongside README.md §3.

#include <stdio.h>

#define N 3   // three replicas

typedef struct {
    int value;     // the replicated value
    int version;   // monotonically increasing version stamp for this value
} Replica;

// Write to a chosen set of replicas (the rest lag behind = not yet replicated).
static void write_to(Replica r[N], const int targets[], int count,
                     int value, int version) {
    for (int i = 0; i < count; i++) {
        r[targets[i]].value   = value;
        r[targets[i]].version = version;
    }
}

// Quorum read: read R replicas, return the value with the HIGHEST version among them.
// Returns the chosen version via *out_version. (Read-repair would then fix stragglers.)
static int quorum_read(const Replica r[N], const int targets[], int R,
                       int *out_version) {
    int best = targets[0];
    for (int i = 1; i < R; i++) {
        if (r[targets[i]].version > r[best].version) best = targets[i];
    }
    *out_version = r[best].version;
    return r[best].value;
}

int main(void) {
    // Start: all three replicas agree on value=10, version=1.
    Replica r[N] = {{10,1},{10,1},{10,1}};
    printf("=== start: 3 replicas, all value=10 version=1 ===\n");
    for (int i = 0; i < N; i++) printf("  R%d: value=%d v%d\n", i, r[i].value, r[i].version);

    // --- The stale-read bug --------------------------------------------------------
    // A write of value=20 reaches the primary (R0) and ONE backup (R1), but R2 lags.
    printf("\n=== a write that has only PARTLY replicated ===\n");
    int w_targets[] = {0, 1};                 // R2 not yet updated
    write_to(r, w_targets, 2, 20, 2);
    printf("  client writes value=20 (v2); reaches R0,R1 — R2 still lagging:\n");
    for (int i = 0; i < N; i++) printf("  R%d: value=%d v%d\n", i, r[i].value, r[i].version);

    // A read served by the single lagging replica R2 returns the OLD value.
    printf("\n=== STALE READ: a client reads only R2 (R=1) ===\n");
    int rt_stale[] = {2};
    int ver;
    int got = quorum_read(r, rt_stale, 1, &ver);
    printf("  read R2 -> value=%d (v%d)  <- STALE: the latest write was 20\n", got, ver);
    printf("  With R=1 and W=2 on N=3: R+W = 3, NOT > N. A read quorum {R2} can miss\n");
    printf("  the write quorum {R0,R1} entirely. No overlap => staleness is possible.\n");

    // --- The quorum fix ------------------------------------------------------------
    // Use R=2, W=2, N=3. Now R + W = 4 > 3, so ANY read pair overlaps the write pair.
    printf("\n=== QUORUM FIX: R=2, W=2, N=3  (R+W=4 > 3) ===\n");
    int rt_q[] = {1, 2};                       // read the two replicas that include the laggard
    got = quorum_read(r, rt_q, 2, &ver);
    printf("  read {R1,R2} -> pick highest version -> value=%d (v%d)\n", got, ver);
    printf("  Even though R2 is stale, R1 is in the read set and carries v2, so the\n");
    printf("  quorum read returns 20. R+W>N guarantees the read set and the write set\n");
    printf("  share at least one node — that node always holds the newest value.\n");

    printf("\n=== takeaways ===\n");
    printf("  - Replication buys fault tolerance but introduces a consistency gap.\n");
    printf("  - A read off a lagging replica can be stale; physical timing won't save you.\n");
    printf("  - R + W > N makes read and write quorums overlap => no stale reads.\n");
    printf("  - Strong vs eventual consistency is largely a choice of R and W.\n");
    return 0;
}
