// Module 42 — Demo 4: Raft-lite — leader election & log replication (a SIMULATION)
//
// Raft (Ongaro & Ousterhout, 2014, "In Search of an Understandable Consensus
// Algorithm", https://raft.github.io/raft.pdf) keeps a replicated log consistent
// across a cluster even when nodes fail. Its two core mechanisms:
//   1. LEADER ELECTION: time is divided into TERMS. A candidate requests votes; a
//      node grants at most one vote per term; a candidate that wins a MAJORITY
//      becomes leader for that term. Majority (> N/2) guarantees a single leader.
//   2. LOG REPLICATION: clients send commands to the leader, which appends them to
//      its log and replicates to followers. Once a MAJORITY has stored an entry, the
//      leader marks it COMMITTED and applies it; committed entries never change.
//
// >>> HONESTY NOTE: this is a TEACHING SIMULATION, not production Raft. <<<
// We model a 5-node cluster as an array driven by a deterministic, single-threaded
// event loop (no randomized timers, no real RPCs/persistence/log-matching/snapshots).
// It faithfully shows terms, vote-majorities, commit-on-majority, and re-election on
// leader failure — enough to build correct intuition. For the real algorithm and all
// safety arguments, read the paper. No randomness => `make run4` is reproducible.
//
// Read top to bottom alongside README.md §4.

#include <stdio.h>

#define N 5   // a 5-node cluster: majority = 3

typedef enum { FOLLOWER, CANDIDATE, LEADER, DOWN } Role;

typedef struct {
    int  id;
    Role role;
    int  current_term;   // latest term this node has seen
    int  voted_for;      // candidate id voted for in current_term (-1 = none)
    int  log_len;        // number of entries this node has stored (toy log)
    int  commit_index;   // highest log index known committed
} Node;

static const char *role_name(Role r) {
    switch (r) {
        case FOLLOWER:  return "follower";
        case CANDIDATE: return "candidate";
        case LEADER:    return "leader";
        case DOWN:      return "DOWN";
    }
    return "?";
}

// A majority of N is any count strictly greater than N/2 (integer division).
static int majority(int n) { return n / 2 + 1; }

// One election in a given term: `candidate` requests votes from all live nodes.
// Each live node votes yes iff it hasn't already voted in this term and the term is
// at least as new as its own. Returns 1 if the candidate won a majority.
static int run_election(Node cluster[N], int candidate, int term) {
    printf("  -- election for term %d, candidate = node %d --\n", term, candidate);
    // The candidate advances to the new term and votes for itself.
    cluster[candidate].role         = CANDIDATE;
    cluster[candidate].current_term = term;
    cluster[candidate].voted_for    = candidate;
    int votes = 0;

    for (int i = 0; i < N; i++) {
        if (cluster[i].role == DOWN) {
            printf("     node %d is DOWN, cannot vote\n", i);
            continue;
        }
        // Reject stale terms; otherwise adopt the term and grant the vote (one per term).
        if (term < cluster[i].current_term) {
            printf("     node %d rejects (its term %d > %d)\n",
                   i, cluster[i].current_term, term);
            continue;
        }
        if (term > cluster[i].current_term) {
            cluster[i].current_term = term;
            cluster[i].voted_for    = -1;      // new term => fresh vote available
            if (i != candidate) cluster[i].role = FOLLOWER;
        }
        if (cluster[i].voted_for == -1 || cluster[i].voted_for == candidate) {
            cluster[i].voted_for = candidate;
            votes++;
            printf("     node %d votes YES for %d  (votes=%d)\n", i, candidate, votes);
        } else {
            printf("     node %d already voted for %d this term\n", i, cluster[i].voted_for);
        }
    }

    int need = majority(N);
    if (votes >= need) {
        cluster[candidate].role = LEADER;
        printf("     => node %d WINS with %d/%d votes (majority is %d) -> LEADER term %d\n",
               candidate, votes, N, need, term);
        for (int i = 0; i < N; i++)
            if (i != candidate && cluster[i].role != DOWN) cluster[i].role = FOLLOWER;
        return 1;
    }
    printf("     => node %d FAILS with %d/%d votes (needed %d)\n",
           candidate, votes, N, need);
    return 0;
}

// The leader appends a command and replicates it; it commits once a majority store it.
static void replicate_entry(Node cluster[N], int leader, const char *cmd) {
    printf("  -- leader %d replicates entry: \"%s\" --\n", leader, cmd);
    cluster[leader].log_len++;                       // leader appends locally first
    int index = cluster[leader].log_len;
    int stored = 1;                                  // the leader has it
    printf("     leader %d appended at log index %d (stored=%d)\n", leader, index, stored);

    for (int i = 0; i < N; i++) {
        if (i == leader || cluster[i].role == DOWN) continue;
        cluster[i].log_len = index;                  // follower stores the entry
        stored++;
        printf("     follower %d stored index %d (stored=%d)\n", i, index, stored);
    }

    int need = majority(N);
    if (stored >= need) {
        for (int i = 0; i < N; i++)
            if (cluster[i].role != DOWN && cluster[i].log_len >= index)
                cluster[i].commit_index = index;
        printf("     => %d/%d stored >= majority %d: entry COMMITTED at index %d\n",
               stored, N, need, index);
    } else {
        printf("     => only %d/%d stored (< majority %d): NOT committed yet\n",
               stored, N, need);
    }
}

static void print_cluster(const Node cluster[N]) {
    for (int i = 0; i < N; i++)
        printf("     node %d: %-9s term=%d log_len=%d commit=%d\n",
               cluster[i].id, role_name(cluster[i].role),
               cluster[i].current_term, cluster[i].log_len, cluster[i].commit_index);
}

int main(void) {
    Node cluster[N];
    for (int i = 0; i < N; i++)
        cluster[i] = (Node){.id = i, .role = FOLLOWER, .current_term = 0,
                            .voted_for = -1, .log_len = 0, .commit_index = 0};

    printf("=== Raft-lite: 5-node cluster, majority = %d ===\n", majority(N));
    printf("    (simulation — see header/README for what this does NOT model)\n\n");

    printf("=== 1. Leader election (term 1) ===\n");
    run_election(cluster, /*candidate=*/0, /*term=*/1);
    printf("\n  cluster state:\n");
    print_cluster(cluster);

    printf("\n=== 2. Log replication & commit-on-majority ===\n");
    replicate_entry(cluster, /*leader=*/0, "SET x = 42");
    printf("\n  cluster state:\n");
    print_cluster(cluster);

    printf("\n=== 3. The leader CRASHES ===\n");
    cluster[0].role = DOWN;
    printf("  node 0 (leader) goes DOWN. Followers stop hearing heartbeats and will\n");
    printf("  time out, starting a new election in a HIGHER term.\n");
    print_cluster(cluster);

    printf("\n=== 4. Re-election in a new term (term 2) ===\n");
    int won = run_election(cluster, /*candidate=*/1, /*term=*/2);
    if (won) {
        printf("\n  node 1 leads term 2; cluster keeps making progress without node 0:\n");
        replicate_entry(cluster, /*leader=*/1, "SET y = 7");
    }
    printf("\n  cluster state:\n");
    print_cluster(cluster);

    printf("\n=== takeaways ===\n");
    printf("  - Terms + one-vote-per-term + majority => at most one leader per term.\n");
    printf("  - An entry is committed only once a MAJORITY stores it; that survives any\n");
    printf("    minority failure (here, losing 1 of 5 still leaves a majority of 4).\n");
    printf("  - On leader failure a follower times out and wins a NEW term — the cluster\n");
    printf("    self-heals as long as a majority is alive. This is the heart of consensus.\n");
    return 0;
}
