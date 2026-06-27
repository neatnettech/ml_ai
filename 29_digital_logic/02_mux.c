// Module 29 — Demo 2: Multiplexers — "choosing a wire"
//
// A multiplexer (mux) picks ONE of several inputs to pass through, based on a
// "select" signal. This is the hardware version of an if/else or array index:
// selection and branching in a CPU are built from muxes. Its inverse, the
// demultiplexer (demux), routes one input to one of several outputs.
//
// Everything here is built from the gates of Demo 1 (themselves built from NAND).
// Build & run: make run2.  Read alongside README.md §2.

#include <stdio.h>

// ---- Primitive + a few gates (same as Demo 1, kept local so each demo stands alone)
static int nand(int a, int b)      { return !(a && b); }
static int gate_not(int a)         { return nand(a, a); }
static int gate_and(int a, int b)  { return gate_not(nand(a, b)); }
static int gate_or(int a, int b)   { return nand(gate_not(a), gate_not(b)); }

// ---- 2:1 MULTIPLEXER ---------------------------------------------------------
// mux(a, b, sel): output a when sel==0, b when sel==1.
//   out = (a AND NOT sel) OR (b AND sel)
// Read it as: "let a through when sel is 0, let b through when sel is 1".
static int mux2(int a, int b, int sel) {
    return gate_or(gate_and(a, gate_not(sel)),
                   gate_and(b, sel));
}

// ---- 4:1 MULTIPLEXER ---------------------------------------------------------
// Choose one of {a,b,c,d} with a 2-bit selector (s1 s0).
// Built as a *tree* of 2:1 muxes — the standard way muxes scale:
//   s0 picks within each pair, s1 picks between the two pair-winners.
static int mux4(int a, int b, int c, int d, int s1, int s0) {
    int lo = mux2(a, b, s0);   // s0 chooses a vs b
    int hi = mux2(c, d, s0);   // s0 chooses c vs d
    return mux2(lo, hi, s1);   // s1 chooses the low pair vs the high pair
}

// ---- 1-bit DEMULTIPLEXER -----------------------------------------------------
// demux(in, sel) routes `in` to out0 (sel==0) or out1 (sel==1); the other is 0.
// We return the two outputs through pointers.
static void demux(int in, int sel, int *out0, int *out1) {
    *out0 = gate_and(in, gate_not(sel));  // active only when sel==0
    *out1 = gate_and(in, sel);            // active only when sel==1
}

int main(void) {
    printf("=== 2:1 mux: out = (sel ? b : a) ===\n");
    printf("  a b sel | out\n");
    for (int sel = 0; sel <= 1; sel++)
        for (int a = 0; a <= 1; a++)
            for (int b = 0; b <= 1; b++)
                printf("  %d %d  %d  |  %d\n", a, b, sel, mux2(a, b, sel));

    printf("\n=== 4:1 mux: (s1 s0) selects one of a,b,c,d ===\n");
    // Use four distinguishable inputs by sweeping which one is 1.
    // Here a=1,b=0,c=0,d=0 etc. would be one test; instead show the selector sweep
    // with fixed inputs a=0,b=1,c=0,d=1 so the chosen value is easy to trace.
    int a = 0, b = 1, c = 0, d = 1;
    printf("  inputs a=%d b=%d c=%d d=%d\n", a, b, c, d);
    printf("  s1 s0 | picks | out\n");
    const char *names[] = {"a", "b", "c", "d"};
    for (int s1 = 0; s1 <= 1; s1++)
        for (int s0 = 0; s0 <= 1; s0++)
            printf("   %d  %d |   %s   |  %d\n",
                   s1, s0, names[(s1 << 1) | s0], mux4(a, b, c, d, s1, s0));

    printf("\n=== 1-bit demux: route `in` to out0 or out1 ===\n");
    printf("  in sel | out0 out1\n");
    for (int in = 0; in <= 1; in++)
        for (int sel = 0; sel <= 1; sel++) {
            int o0, o1;
            demux(in, sel, &o0, &o1);
            printf("  %d   %d  |   %d    %d\n", in, sel, o0, o1);
        }

    printf("\nA mux is selection in hardware: it's how a CPU chooses which value\n");
    printf("flows onto a bus, and the seed of conditional execution (branching).\n");
    return 0;
}
