// Module 35 — Demo 2: mmap — mapping memory and files into the address space
//
// malloc gives you bytes; mmap gives you whole PAGES wired straight into your
// address space by the kernel. Two uses here:
//   (1) anonymous mapping  — raw zeroed pages, the building block malloc uses
//   (2) file mapping       — a file's bytes appear as memory; writes go to the file
//
// Demand paging: mmap reserves the address range but the kernel doesn't load (or
// allocate) a physical page until you first TOUCH it — a page fault pulls it in.
//
// Build & run with: make run2   (creates and removes a temp file under /tmp).
//
// Read top to bottom alongside README.md §2.

#define _DARWIN_C_SOURCE   // expose MAP_ANON family cleanly on macOS; harmless elsewhere

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>

int main(void) {
    long page = sysconf(_SC_PAGESIZE);
    printf("=== mmap: one page of anonymous memory ===\n");
    printf("  page size = %ld bytes\n", page);

    // (1) Anonymous mapping: not backed by any file — just zeroed RAM pages.
    size_t len = (size_t)page;
    char *mem = mmap(NULL, len, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANON, -1, 0);
    if (mem == MAP_FAILED) { perror("mmap anon"); return 1; }
    printf("  mapped %zu bytes at %p (kernel chose the address)\n", len, (void *)mem);
    printf("  first byte before writing = %d (anonymous pages start zeroed)\n", mem[0]);

    strcpy(mem, "hello from an anonymous mapping");
    printf("  wrote + read back: \"%s\"\n", mem);

    if (munmap(mem, len) != 0) { perror("munmap"); return 1; }
    printf("  unmapped; that address range is no longer ours.\n");

    // (2) File mapping: write through memory, read back from the file.
    const char *path = "/tmp/m35_mmap_demo.txt";
    const char *msg  = "mmap wrote this straight into the file\n";
    size_t mlen = strlen(msg);

    printf("\n=== mmap: a file mapped into memory ===\n");
    int fd = open(path, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    // The file must be at least as large as the region we map, so size it first.
    if (ftruncate(fd, (off_t)mlen) != 0) { perror("ftruncate"); close(fd); return 1; }

    char *fmap = mmap(NULL, mlen, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (fmap == MAP_FAILED) { perror("mmap file"); close(fd); return 1; }

    memcpy(fmap, msg, mlen);          // a store to memory == a write to the file
    msync(fmap, mlen, MS_SYNC);       // flush the dirty pages to disk
    munmap(fmap, mlen);
    close(fd);
    printf("  wrote %zu bytes to %s via the mapping (no write() call).\n", mlen, path);

    // Prove it landed: read the file back the ordinary way.
    char buf[128] = {0};
    fd = open(path, O_RDONLY);
    if (fd < 0) { perror("reopen"); return 1; }
    ssize_t got = read(fd, buf, sizeof buf - 1);
    close(fd);
    if (got < 0) { perror("read"); return 1; }
    printf("  read it back with read(): \"%.*s\"", (int)got, buf);

    if (unlink(path) != 0) { perror("unlink"); return 1; }
    printf("  (temp file removed)\n");

    printf("\n=== Demand paging (the idea) ===\n");
    printf("  mmap reserved the addresses immediately, but a physical page is only\n");
    printf("  allocated when you first touch it -- a page fault traps to the kernel,\n");
    printf("  which maps a page, then your instruction re-runs. You can map a file\n");
    printf("  far larger than RAM and pay only for the pages you actually read.\n");
    return 0;
}
