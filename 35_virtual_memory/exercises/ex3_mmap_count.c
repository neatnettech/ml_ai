// Exercise 35.3 — Count newlines in a memory-mapped file
//
// The scaffold below creates a small temp file, opens it, and stat()s its size.
// Your job: mmap the whole file READ-ONLY, then count the newline ('\n') bytes by
// scanning the mapping like a plain char array — no read() calls. Also report the
// byte count (that's just the file size). Then munmap, close, and remove the file.
//
// TODO markers show exactly where to fill in. Verify with `make ex3`: it must print
//   bytes = 34, lines = 3
// Solution in ../solutions/ex3_mmap_count.c; README §6.

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

    // Set up a known input file.
    int fd = open(path, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    if (write(fd, contents, strlen(contents)) < 0) { perror("write"); close(fd); return 1; }

    struct stat st;
    if (fstat(fd, &st) != 0) { perror("fstat"); close(fd); return 1; }
    size_t len = (size_t)st.st_size;

    // TODO: mmap `len` bytes of `fd` as PROT_READ, MAP_PRIVATE, offset 0.
    //       Check for MAP_FAILED.
    const char *map = NULL;   // replace with your mmap() result

    // TODO: count '\n' bytes by scanning map[0..len).
    size_t lines = 0;
    (void)map;   // remove once you use the mapping

    printf("  bytes = %zu, lines = %zu\n", len, lines);

    // TODO: munmap(the mapping, len).
    close(fd);
    if (unlink(path) != 0) { perror("unlink"); return 1; }
    return 0;
}
