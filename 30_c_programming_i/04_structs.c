// Module 30 — Demo 4: structs, pass by value vs pointer, ->, and padding
//
// A struct groups related fields into one object. You can pass a struct by VALUE
// (a full copy) or by POINTER (cheap, and lets you mutate the original). The `->`
// operator is just sugar for "dereference, then take a field". The compiler also
// inserts PADDING so fields land on aligned addresses. Build & run: make run4
//
// Read top to bottom alongside README.md §4.

#include <stdio.h>
#include <string.h>

struct Point {
    int x;
    int y;
};

struct Person {
    char name[16];  // small fixed buffer so the struct is self-contained
    int  age;
    struct Point home;  // structs can nest
};

// pass by VALUE: receives a COPY; changes don't escape.
static void move_by_value(struct Point p) {
    p.x += 100;  // mutates the copy only
}

// pass by POINTER: receives the address; (*ptr).field, or the nicer ptr->field.
static void move_by_pointer(struct Point *p) {
    p->x += 100;  // p->x is exactly (*p).x — follow the pointer, then field x
    p->y += 100;
}

static void print_point(const char *label, struct Point p) {
    printf("  %s = (%d, %d)\n", label, p.x, p.y);
}

int main(void) {
    printf("=== Building and using a struct ===\n");
    struct Point a = {3, 4};        // positional init
    struct Point b = {.x = 10, .y = 20};  // designated init (C99+)
    print_point("a", a);
    print_point("b", b);

    printf("\n=== pass by value vs by pointer ===\n");
    move_by_value(a);
    print_point("a after move_by_value", a);     // unchanged: copy was moved
    move_by_pointer(&a);
    print_point("a after move_by_pointer", a);    // changed via address

    printf("\n=== the -> operator ===\n");
    struct Point *pp = &b;
    printf("  pp->x = %d, (*pp).x = %d  (identical syntaxes)\n", pp->x, (*pp).x);

    printf("\n=== nested struct + an array of structs ===\n");
    struct Person crew[2];
    strcpy(crew[0].name, "Ada");   // name is a char array; copy into it
    crew[0].age = 36;
    crew[0].home = (struct Point){1, 2};
    strcpy(crew[1].name, "Grace");
    crew[1].age = 44;
    crew[1].home = (struct Point){3, 4};
    for (size_t i = 0; i < sizeof crew / sizeof *crew; i++) {
        printf("  crew[%zu]: %-6s age %d, home (%d,%d)\n",
               i, crew[i].name, crew[i].age, crew[i].home.x, crew[i].home.y);
    }

    printf("\n=== sizeof, padding, and alignment ===\n");
    // Point has two ints = 8 bytes, no padding needed.
    printf("  sizeof(struct Point)  = %zu  (two ints, tightly packed)\n",
           sizeof(struct Point));
    // Person: name[16] + int age + Point(8). The compiler may pad so each field is
    // aligned (ints on 4-byte boundaries) and the whole struct's size is a multiple
    // of its largest alignment — so sizeof can exceed the raw field-byte total.
    size_t raw = sizeof(((struct Person *)0)->name)
               + sizeof(((struct Person *)0)->age)
               + sizeof(((struct Person *)0)->home);
    printf("  sum of field sizes    = %zu bytes\n", raw);
    printf("  sizeof(struct Person) = %zu  (>= the sum; here the fields already align)\n",
           sizeof(struct Person));
    // Reorder fields and the padding can change: e.g. `char c; int i; char d;`
    // is usually 12 bytes, not 6, because the int must sit on a 4-byte boundary.
    struct Padded { char c; int i; char d; };
    printf("  struct{char;int;char} = %zu bytes (padded for the int's alignment)\n",
           sizeof(struct Padded));

    return 0;
}
