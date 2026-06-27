// SOLUTION 30.2 — A singly linked list (structs + malloc + pointers)

#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int          value;
    struct Node *next;
} Node;

Node *push_front(Node *head, int value) {
    Node *node = malloc(sizeof *node);
    if (node == NULL) {
        perror("malloc");
        exit(EXIT_FAILURE);
    }
    node->value = value;
    node->next  = head;   // the old head becomes the second node
    return node;          // the new node is the new head
}

size_t length(const Node *head) {
    size_t n = 0;
    for (const Node *p = head; p != NULL; p = p->next) {
        n++;
    }
    return n;
}

void free_list(Node *head) {
    while (head != NULL) {
        Node *next = head->next;  // save next BEFORE freeing head
        free(head);
        head = next;
    }
}

static void print_list(const Node *head) {
    printf("  list: ");
    for (const Node *p = head; p != NULL; p = p->next) {
        printf("%d -> ", p->value);
    }
    printf("NULL\n");
}

int main(void) {
    Node *head = NULL;
    head = push_front(head, 3);
    head = push_front(head, 2);
    head = push_front(head, 1);
    print_list(head);
    printf("  length = %zu\n", length(head));
    free_list(head);
    printf("  freed.\n");
    return 0;
}
