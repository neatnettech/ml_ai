// Module 31 — Demo 2: FUNCTION POINTERS
//
// A function name decays to the ADDRESS of its code, just like an array name decays
// to a pointer. So you can store a function in a variable, put it in a table, or
// pass it to another function as a CALLBACK. This is how C does polymorphism: one
// generic routine, behavior supplied by the caller. Build & run with: make run2
// Read alongside README.md §2.

#include <stdio.h>
#include <stdlib.h>   // qsort
#include <string.h>   // strcmp

// ---- 1. A function pointer as a variable ---------------------------------------
// Three functions with the SAME signature int(int,int) so one pointer fits any.
static int add(int a, int b) { return a + b; }
static int sub(int a, int b) { return a - b; }
static int mul(int a, int b) { return a * b; }

// ---- 2. A DISPATCH TABLE: array of {name, function} ----------------------------
// Look up behavior by string — the C idiom behind command interpreters, opcode
// tables, plugin systems. `int (*fn)(int,int)` reads: "fn is a pointer to a
// function taking (int,int) and returning int".
struct op {
    const char *name;
    int (*fn)(int, int);
};

static const struct op OPS[] = {
    {"add", add},
    {"sub", sub},
    {"mul", mul},
};

static int dispatch(const char *name, int a, int b, int *out) {
    for (size_t i = 0; i < sizeof OPS / sizeof OPS[0]; i++) {
        if (strcmp(OPS[i].name, name) == 0) {
            *out = OPS[i].fn(a, b);   // call through the pointer
            return 1;                 // found
        }
    }
    return 0;                         // unknown op
}

// ---- 3. A CALLBACK: pass behavior into a generic routine -----------------------
// map() applies a caller-supplied function to every element. The function pointer
// `int (*f)(int)` is the parameter — map() itself knows nothing about the work.
static void map(int *arr, size_t n, int (*f)(int)) {
    for (size_t i = 0; i < n; i++) arr[i] = f(arr[i]);
}
static int square(int x) { return x * x; }
static int negate(int x) { return -x; }

// ---- 4. qsort from <stdlib.h>: the standard library's own callback -------------
// qsort is fully generic over byte arrays; YOU supply the comparator. The
// comparator receives const void* (pointers to two elements) and returns
// <0 / 0 / >0. We cast back to the real type inside.
static int cmp_int_asc(const void *pa, const void *pb) {
    int a = *(const int *)pa;
    int b = *(const int *)pb;
    return (a > b) - (a < b);   // branchless -1/0/1; avoids a-b overflow
}
static int cmp_int_desc(const void *pa, const void *pb) {
    return cmp_int_asc(pb, pa); // reverse the order by swapping args
}

static void print_arr(const char *label, const int *a, size_t n) {
    printf("  %s", label);
    for (size_t i = 0; i < n; i++) printf(" %d", a[i]);
    putchar('\n');
}

int main(void) {
    printf("=== dispatch table (lookup behavior by name) ===\n");
    const char *names[] = {"add", "mul", "sub", "div"};
    for (size_t i = 0; i < sizeof names / sizeof names[0]; i++) {
        int r;
        if (dispatch(names[i], 6, 4, &r))
            printf("  %s(6, 4) = %d\n", names[i], r);
        else
            printf("  %s: unknown op\n", names[i]);
    }

    printf("\n=== map: apply a callback to every element ===\n");
    int xs[] = {1, 2, 3, 4, 5};
    size_t n = sizeof xs / sizeof xs[0];
    print_arr("start:  ", xs, n);
    map(xs, n, square);
    print_arr("square: ", xs, n);
    map(xs, n, negate);
    print_arr("negate: ", xs, n);

    printf("\n=== qsort with a custom comparator ===\n");
    int data[] = {5, 2, 9, 1, 7, 3};
    n = sizeof data / sizeof data[0];
    print_arr("unsorted:   ", data, n);
    qsort(data, n, sizeof data[0], cmp_int_asc);
    print_arr("ascending:  ", data, n);
    qsort(data, n, sizeof data[0], cmp_int_desc);
    print_arr("descending: ", data, n);

    return 0;
}
