// SOLUTION 35.3 — Count newlines in a memory-mapped file

#define _DARWIN_C_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>

int main(void) {
    const char *path = "/tmp/m35_ex3_count.txt";
    const char *contents = "first line\nsecond line\nthird line\n";  // 34 bytes, 3 \n

    int fd = open(path, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    if (write(fd, contents, strlen(contents)) < 0) { perror("write"); close(fd); return 1; }

    struct stat st;
    if (fstat(fd, &st) != 0) { perror("fstat"); close(fd); return 1; }
    size_t len = (size_t)st.st_size;

    const char *map = mmap(NULL, len, PROT_READ, MAP_PRIVATE, fd, 0);
    if (map == MAP_FAILED) { perror("mmap"); close(fd); return 1; }

    size_t lines = 0;
    for (size_t i = 0; i < len; i++) {
        if (map[i] == '\n') lines++;
    }

    printf("  bytes = %zu, lines = %zu\n", len, lines);

    munmap((void *)map, len);
    close(fd);
    if (unlink(path) != 0) { perror("unlink"); return 1; }
    return 0;
}
