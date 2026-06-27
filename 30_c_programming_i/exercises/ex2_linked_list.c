// Exercise 30.2 — A singly linked list (structs + malloc + pointers)
//
// A linked list is a chain of heap nodes, each holding a value and a pointer to the
// next node. The list itself is just a pointer to the first node (the "head"); an
// empty list is a NULL head.
//
// Implement push_front, length, and free_list. Then `make ex2` should match the
// expected output in README.md §6. Solution in ../solutions/ex2_linked_list.c.

#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int          value;
    struct Node *next;   // pointer to the next node, or NULL at the end
} Node;

// Insert `value` at the FRONT and return the new head. (Front insert is O(1):
// allocate a node, point its next at the old head, return it as the new head.)
Node *push_front(Node *head, int value) {
    // TODO: malloc a Node (check for NULL), set its value and its next = head,
    // then return the new node as the new head.
    (void)value;
    return head;  // replace this
}

// Count the nodes by walking from head to NULL.
size_t length(const Node *head) {
    // TODO: walk a cursor from head following ->next until NULL, counting nodes.
    (void)head;
    return 0;  // replace this
}

// Free every node. You MUST save next BEFORE freeing the current node, or you'd
// read freed memory to find the rest of the list.
void free_list(Node *head) {
    // TODO: while head != NULL: remember next = head->next, free(head), head = next.
    (void)head;
}

static void print_list(const Node *head) {
    printf("  list: ");
    for (const Node *p = head; p != NULL; p = p->next) {
        printf("%d -> ", p->value);
    }
    printf("NULL\n");
}

int main(void) {
    Node *head = NULL;  // empty list
    head = push_front(head, 3);
    head = push_front(head, 2);
    head = push_front(head, 1);  // pushing front reverses insertion order
    print_list(head);
    printf("  length = %zu\n", length(head));
    free_list(head);  // no leaks
    printf("  freed.\n");
    return 0;
}
