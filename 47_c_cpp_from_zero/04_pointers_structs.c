/* Module 47 — Demo 4: the heart of C — pointers, structs, and the heap.
 *
 * A pointer is a variable that holds an ADDRESS of another value.
 *   &x   "address of x"
 *   *p   "the value p points at" (dereference)
 * Passing an address lets a function change the caller's variable (compare with
 * demo 3's pass-by-value). A struct groups related fields into one type; you
 * reach fields with `.` on a value or `->` through a pointer. malloc grabs
 * memory from the heap that lives until you free it — every malloc needs exactly
 * one free.
 *
 * This is the operational view. For the full stack/heap/memory model at the
 * hardware level, see Module 30 — C Programming I.
 */
#include <stdio.h>
#include <stdlib.h>

/* takes an address, so it mutates the caller's variable */
void add_one(int *p) { *p += 1; }

struct Point { int x, y; };

/* -> through a pointer to a struct */
int dist_sq_from_origin(const struct Point *p) {
    return p->x * p->x + p->y * p->y;
}

int main(void) {
    printf("=== pointers ===\n");
    int x = 10;
    printf("  x = %d, &x is an address, *(&x) = %d\n", x, *(&x));
    add_one(&x);
    printf("  after add_one(&x): x = %d\n", x);

    printf("=== structs ===\n");
    struct Point p = {3, 4};
    printf("  Point{ x=%d, y=%d }  distance-from-origin squared = %d\n",
           p.x, p.y, dist_sq_from_origin(&p));

    printf("=== malloc/free: a heap array of 5 ints ===\n");
    int n = 5;
    int *heap = malloc((size_t)n * sizeof(int));
    if (heap == NULL) return 1;           /* always check malloc */
    for (int i = 0; i < n; i++) heap[i] = i * 10;
    printf("  heap[0..4] =");
    for (int i = 0; i < n; i++) printf(" %d", heap[i]);
    printf("\n");
    free(heap);
    printf("  freed. (every malloc needs exactly one free)\n");
    return 0;
}
