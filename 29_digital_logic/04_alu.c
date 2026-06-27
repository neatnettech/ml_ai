// Module 29 — Demo 4: A tiny ALU — the arithmetic/logic heart of a CPU
//
// An ALU (Arithmetic Logic Unit) takes two N-bit operands plus a few "op-select"
// control bits and produces a result + status flags. It is the datapath block that
// actually *computes* in a processor. We support 4 operations chosen by 2 op bits:
//
//   op  operation
//   00  a AND b
//   01  a OR  b
//   10  a + b      (ripple-carry adder)
//   11  a - b      (a + two's-complement of b)
//
// and we output two flags: ZERO (result is all zeros) and NEGATIVE (top/sign bit).
// Build & run: make run4.  Read alongside README.md §4.
//
// Bits are arrays of int (0/1), index 0 = LSB. N is fixed at 8 here.

#include <stdio.h>

#define N 8

// ---- gates from NAND (local copy so the demo stands alone) -------------------
static int nand(int a, int b)      { return !(a && b); }
static int gate_not(int a)         { return nand(a, a); }
static int gate_and(int a, int b)  { return gate_not(nand(a, b)); }
static int gate_or(int a, int b)   { return nand(gate_not(a), gate_not(b)); }
static int gate_xor(int a, int b)  { int c = nand(a, b); return nand(nand(a, c), nand(b, c)); }
static int mux2(int a, int b, int s) { return gate_or(gate_and(a, gate_not(s)), gate_and(b, s)); }

// ---- adder (from Demo 3) -----------------------------------------------------
static void full_adder(int a, int b, int cin, int *sum, int *cout) {
    int s1 = gate_xor(a, b);
    int c1 = gate_and(a, b);
    *sum   = gate_xor(s1, cin);
    int c2 = gate_and(s1, cin);
    *cout  = gate_or(c1, c2);
}
static int ripple_add(const int *a, const int *b, int *out, int cin) {
    int carry = cin;
    for (int i = 0; i < N; i++) full_adder(a[i], b[i], carry, &out[i], &carry);
    return carry;
}

// ---- THE ALU -----------------------------------------------------------------
// op1 op0 select the operation (see table at top). We compute all four candidate
// results and then a per-bit mux tree selects the chosen one — this mirrors real
// hardware, where every unit computes in parallel and a mux picks the output.
typedef struct { int bits[N]; int zero; int negative; } AluResult;

static AluResult alu(const int *a, const int *b, int op1, int op0) {
    AluResult r;

    // Candidate 1: bitwise AND and OR (computed bit-by-bit).
    int and_res[N], or_res[N];
    for (int i = 0; i < N; i++) {
        and_res[i] = gate_and(a[i], b[i]);
        or_res[i]  = gate_or(a[i], b[i]);
    }

    // Candidate 2: a + b.
    int add_res[N];
    ripple_add(a, b, add_res, 0);

    // Candidate 3: a - b == a + (~b) + 1.
    int nb[N], sub_res[N];
    for (int i = 0; i < N; i++) nb[i] = gate_not(b[i]);
    ripple_add(a, nb, sub_res, 1);

    // Select the result with a 4:1 mux per bit, driven by (op1, op0):
    //   00->AND  01->OR  10->ADD  11->SUB
    for (int i = 0; i < N; i++) {
        int lo = mux2(and_res[i], or_res[i], op0);  // op0 picks AND vs OR
        int hi = mux2(add_res[i], sub_res[i], op0); // op0 picks ADD vs SUB
        r.bits[i] = mux2(lo, hi, op1);              // op1 picks logic vs arithmetic
    }

    // ZERO flag: 1 iff every result bit is 0. OR-reduce the bits, then invert.
    int any = 0;
    for (int i = 0; i < N; i++) any = gate_or(any, r.bits[i]);
    r.zero = gate_not(any);

    // NEGATIVE flag: the sign bit (MSB) in two's complement.
    r.negative = r.bits[N - 1];

    return r;
}

// ---- helpers -----------------------------------------------------------------
static void to_bits(unsigned v, int *bits) { for (int i = 0; i < N; i++) bits[i] = (v >> i) & 1u; }
static unsigned from_bits(const int *bits)  { unsigned v = 0; for (int i = 0; i < N; i++) v |= (unsigned)bits[i] << i; return v; }
static void print_bits(const int *bits)     { for (int i = N - 1; i >= 0; i--) putchar(bits[i] ? '1' : '0'); }
// Interpret the 8 result bits as a signed two's-complement value for display.
static int as_signed(const int *bits) {
    unsigned u = from_bits(bits);
    return (u & 0x80u) ? (int)u - 256 : (int)u;
}

int main(void) {
    const char *opname[] = {"AND", "OR ", "ADD", "SUB"};

    printf("=== Tiny 8-bit ALU: operands a=20, b=5 ===\n");
    int a[N], b[N];
    to_bits(20, a);
    to_bits(5, b);
    printf("  a = "); print_bits(a); printf("  (%u)\n", from_bits(a));
    printf("  b = "); print_bits(b); printf("  (%u)\n\n", from_bits(b));

    printf("  op  name | result          uns  sgn | Z N\n");
    for (int op1 = 0; op1 <= 1; op1++)
        for (int op0 = 0; op0 <= 1; op0++) {
            AluResult r = alu(a, b, op1, op0);
            printf("  %d%d  %s | ", op1, op0, opname[(op1 << 1) | op0]);
            print_bits(r.bits);
            printf("  %3u  %4d | %d %d\n",
                   from_bits(r.bits), as_signed(r.bits), r.zero, r.negative);
        }

    printf("\n=== Flags in action: 7 - 7 sets ZERO; 5 - 9 sets NEGATIVE ===\n");
    to_bits(7, a); to_bits(7, b);
    AluResult z = alu(a, b, 1, 1);  // SUB
    printf("  7 - 7 = %d   Z=%d N=%d\n", as_signed(z.bits), z.zero, z.negative);
    to_bits(5, a); to_bits(9, b);
    AluResult n = alu(a, b, 1, 1);  // SUB
    printf("  5 - 9 = %d  Z=%d N=%d\n", as_signed(n.bits), n.zero, n.negative);

    printf("\nThis ALU + a set of REGISTERS (built from flip-flops, which store a bit)\n");
    printf("+ a control unit that runs the fetch-decode-execute loop = a CPU. See\n");
    printf("README.md section 5 for how those pieces fit together.\n");
    return 0;
}
