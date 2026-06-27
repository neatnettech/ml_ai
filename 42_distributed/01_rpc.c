// Module 42 — Demo 1: RPC, dropped/duplicated messages, and delivery semantics
//
// A Remote Procedure Call (RPC) makes a call on another machine LOOK like a local
// function call — but it travels over an unreliable network, so the illusion leaks.
// We model the whole thing in one process: the "network" is a function that carries
// a Message struct from a client to a server handler. Then we INJECT the two failures
// every RPC system must survive — a dropped reply and a duplicated request — and show
// why RPC needs (a) timeouts + retries and (b) idempotency to make retries safe.
//
// Fully deterministic: failures are scripted, not random. Build & run: make run1
//
// Read top to bottom alongside README.md §1.

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

// ---- The server: a bank account with a "deposit" RPC ----------------------------
// The handler is the "remote procedure". `request_id` lets the server DEDUPLICATE
// retries: at-most-once semantics = remember which requests we already applied.

typedef struct {
    int     balance;          // server-side state
    uint32_t last_applied_id; // highest request_id already applied (0 = none)
} Server;

// at-LEAST-once handler: applies the deposit every time it is called. Safe to retry
// ONLY if the operation is idempotent; a deposit is NOT, so duplicates double-count.
static int deposit_at_least_once(Server *s, int amount) {
    s->balance += amount;
    return s->balance;
}

// at-MOST-once handler: ignores a request_id it has already applied. A duplicate
// request returns the same answer without changing state — retries become safe.
static int deposit_at_most_once(Server *s, uint32_t request_id, int amount) {
    if (request_id <= s->last_applied_id) {
        printf("    [server] request #%u already applied, ignoring duplicate\n",
               request_id);
        return s->balance;            // re-send the original result, no state change
    }
    s->balance += amount;
    s->last_applied_id = request_id;
    return s->balance;
}

int main(void) {
    printf("=== 1. A normal RPC: request -> handler -> response ===\n");
    Server s = {.balance = 100, .last_applied_id = 0};
    printf("  client: deposit(+50)\n");
    int reply = deposit_at_least_once(&s, 50);
    printf("  server replies: balance = %d   (the RPC \"returned\")\n\n", reply);

    printf("=== 2. The network DROPS the reply ===\n");
    printf("  client: deposit(+50)\n");
    reply = deposit_at_least_once(&s, 50);          // server applied it: 150 -> 200
    printf("  server applied it: balance = %d\n", reply);
    printf("  ...but the reply packet is LOST. The client waits, hears nothing.\n");
    printf("  The client cannot tell \"request lost\" from \"reply lost\" — so it must\n");
    printf("  use a TIMEOUT and then RETRY. Watch what a blind retry does next.\n\n");

    printf("=== 3. Blind retry with at-LEAST-once (no dedup) — double-counts! ===\n");
    printf("  client times out, retries: deposit(+50)\n");
    reply = deposit_at_least_once(&s, 50);          // applied AGAIN: 200 -> 250
    printf("  server applied it AGAIN: balance = %d  <- BUG: +50 counted twice\n", reply);
    printf("  balance is now 250, but the user only meant to deposit +50 twice (200).\n\n");

    printf("=== 4. Same scenario with at-MOST-once (request_id dedup) ===\n");
    Server s2 = {.balance = 100, .last_applied_id = 0};
    uint32_t req = 7;                               // the client picks a unique id
    printf("  client: deposit(+50), request #%u\n", req);
    reply = deposit_at_most_once(&s2, req, 50);     // applied once: 100 -> 150
    printf("  server applied it: balance = %d\n", reply);
    printf("  ...reply is LOST. Client times out and RETRIES the SAME request #%u:\n", req);
    reply = deposit_at_most_once(&s2, req, 50);     // duplicate: ignored
    printf("  server reply: balance = %d  <- correct: retry was safe (idempotent)\n\n",
           reply);

    printf("=== takeaways ===\n");
    printf("  - RPC hides the network, but the network can drop/duplicate/reorder.\n");
    printf("  - A lost reply is indistinguishable from a lost request => need TIMEOUT+RETRY.\n");
    printf("  - Retries make a request arrive >= once (at-least-once). To stay correct,\n");
    printf("    either the op is naturally idempotent, OR the server dedups by request id\n");
    printf("    (at-most-once). \"Exactly-once\" = at-least-once delivery + dedup.\n");
    return 0;
}
