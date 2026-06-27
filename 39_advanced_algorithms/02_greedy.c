// Module 39 — Demo 2: Greedy algorithms — interval scheduling (activity selection)
//
// You have n activities, each with a start and finish time, and one room. You can run
// two activities only if they don't overlap. Goal: schedule as MANY activities as
// possible. The greedy rule is almost too simple: repeatedly pick the activity that
// FINISHES EARLIEST among those that still fit. Sort by finish time, then sweep once.
//
// Why is "earliest finish" optimal? (Exchange argument, see README §2.) Let the greedy
// pick its first activity g (earliest finish overall). Take ANY optimal schedule and
// let its first activity be o. Because g finishes no later than o, swapping o for g
// cannot cause a conflict with the rest of the optimal schedule — so we get another
// optimal schedule that starts with g. Recurse on the activities that start after g
// finishes. By induction the greedy choice is always part of *some* optimal solution,
// so greedy is optimal. (A greedy that maximizes total time, or picks shortest first,
// is NOT optimal — order matters, and the proof tells you which order.)
//
// Build & run with: make run2.  Read alongside README.md §2.

#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int id;
    int start;
    int finish;
} Activity;

// Sort comparator: by finish time ascending. (qsort needs void* signatures.)
static int by_finish(const void *pa, const void *pb) {
    const Activity *a = pa, *b = pb;
    if (a->finish != b->finish) return a->finish - b->finish;
    return a->start - b->start;
}

int main(void) {
    Activity acts[] = {
        {1,  1,  4},
        {2,  3,  5},
        {3,  0,  6},
        {4,  5,  7},
        {5,  3,  9},
        {6,  5,  9},
        {7,  6, 10},
        {8,  8, 11},
        {9,  8, 12},
        {10, 2, 14},
        {11, 12, 16},
    };
    int n = (int)(sizeof acts / sizeof *acts);

    printf("=== Interval scheduling: pick the most non-overlapping activities ===\n\n");
    printf("  activities (id: [start, finish)):\n   ");
    for (int i = 0; i < n; i++) printf(" %d:[%d,%d)", acts[i].id, acts[i].start, acts[i].finish);
    printf("\n\n");

    // Greedy core: sort by finish, then take each activity whose start is >= the
    // finish of the last one we took.
    qsort(acts, (size_t)n, sizeof *acts, by_finish);

    printf("  sorted by finish time, then greedily take earliest-finishing that fits:\n");
    int *chosen = malloc((size_t)n * sizeof *chosen);
    int count = 0;
    int last_finish = -1;
    for (int i = 0; i < n; i++) {
        if (acts[i].start >= last_finish) {
            chosen[count++] = acts[i].id;
            last_finish = acts[i].finish;
            printf("    take id %d  [%d,%d)\n", acts[i].id, acts[i].start, acts[i].finish);
        }
    }

    printf("\n  chosen %d activities:", count);
    for (int i = 0; i < count; i++) printf(" %d", chosen[i]);
    printf("\n  (no two overlap; no schedule of this input fits more than %d)\n", count);

    free(chosen);
    return 0;
}
