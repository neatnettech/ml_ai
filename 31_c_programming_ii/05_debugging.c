// Module 31 — Demo 5: DEBUGGING with gdb/lldb and valgrind
//
// This program runs CORRECTLY as shipped. It is a guided tour: the function
// sum_to_n once had a classic off-by-one bug (documented below), and the comments
// walk you through how a debugger and a memory checker would have caught it.
// Build & run with: make run5. Build with symbols (-g, already in CFLAGS) so the
// debugger can show source lines.
//
// Read alongside README.md §5, which has the full lldb/gdb/valgrind transcripts.

#include <stdio.h>
#include <stdlib.h>

// --- The bug that WAS here (now fixed) ------------------------------------------
// The loop once read `for (int i = 0; i <= n; i++)` and indexed a[i], walking ONE
// element past the array — an out-of-bounds read (UB; see demo 4). Under lldb you
// would `break sum_to_n`, `run`, then `next` / `print i` to watch i reach n and
// step off the end. Under valgrind (Linux/container) the bad read prints
// "Invalid read of size 4" with the exact line. The fix is the correct bound `< n`.
static long sum_array(const int *a, int n) {
    long total = 0;
    for (int i = 0; i < n; i++) {   // FIXED: `< n`, not `<= n`
        total += a[i];
    }
    return total;
}

// A second routine that allocates, to show the valgrind leak workflow. As written
// it frees correctly; comment out the free() and valgrind reports the leak with a
// stack trace to this malloc — see README §5.
static int *make_range(int n) {
    int *r = malloc((size_t)n * sizeof *r);
    if (!r) return NULL;
    for (int i = 0; i < n; i++) r[i] = i + 1;
    return r;
}

int main(void) {
    int data[] = {3, 1, 4, 1, 5, 9, 2, 6};
    int n = (int)(sizeof data / sizeof data[0]);

    printf("=== sum_array ===\n");
    printf("  sum of %d elements = %ld  (expected 31)\n", n, sum_array(data, n));

    printf("\n=== make_range + free ===\n");
    int *r = make_range(5);
    if (r) {
        printf("  range:");
        for (int i = 0; i < 5; i++) printf(" %d", r[i]);
        putchar('\n');
        free(r);                    // remove this line to demo a leak under valgrind
    }

    printf("\nTo practice: see README §5 for the lldb session and the valgrind run\n");
    printf("(valgrind lives in the x86-64 container; lldb is native on macOS).\n");
    return 0;
}
