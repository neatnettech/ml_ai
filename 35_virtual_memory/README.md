# Module 35 — Virtual Memory & Allocation

**Purpose:** Every process believes it owns a private, contiguous address space that
starts at zero and runs to the top of the machine — a comfortable fiction the kernel
and the MMU maintain by translating *virtual* addresses to *physical* RAM, one page
at a time. This module makes that fiction visible: you'll print the address of each
region of your own process, map raw pages and files into your address space with
`mmap`, watch the heap fragment, and finally **build your own `malloc`/`free`** over
a static byte buffer. By the end you'll know what `malloc` actually does and why
"out of memory" rarely means "out of bytes."

**Prerequisites:** Module 30 (C pointers and `malloc`) and Module 34 (linking &
loading — how the segments you'll print here got placed in the first place). C is
assumed at the level of those modules; we introduce the POSIX VM calls as we use them.

**What you'll learn:**
- The **process address space**: text, data, bss, heap, stack — what lives where and which way each grows
- **ASLR**: why the addresses change every run, and what that defends against
- **`mmap`**: mapping anonymous pages and files; **demand paging** and why a page is the unit
- **Fragmentation**: why free space that isn't *contiguous* can't satisfy a large request
- **How `malloc` is built**: block headers, a free list, first-fit, splitting, and **coalescing**

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 35 runs **natively on Apple Silicon** — no container needed. The `mmap` demos
use POSIX (`mmap`/`munmap`/`getpagesize`), which work as-is on macOS; we `#define
_DARWIN_C_SOURCE` in the two files that touch `MAP_ANON` so the build stays clean and
portable. You only need `clang` + `make` (Xcode Command Line Tools):

```bash
make run        # build + run all four demos
```

Temp files for the `mmap` demos are created under `/tmp` and removed by the programs
themselves; `make clean` also sweeps them just in case.

> **Note on addresses:** every address printed below is from a real run on this
> machine. **They will differ on yours and between runs** — that's ASLR (§1), not a
> bug. What stays constant is the *ordering* and the *relationships*.

---

## 1. The process address space

A running process is laid out in regions: **text** (machine code), **data**
(initialized globals), **bss** (zeroed globals), the **heap** (grows up, fed by
`malloc`), and the **stack** (grows down, holds locals). [`01_address_space.c`](01_address_space.c)
prints one address from each (`make run1`):

```
=== One process, five regions (low address -> high) ===
  text   (code)        0x104b50734   a_function
  data   (init global) 0x104b58000   g_initialized=42
  bss    (zero global) 0x104b58004   g_uninitialized=0
  heap   (malloc)      0x105312220   *heap=99
  stack  (local)       0x16b2ae4a8   local=7
```

Read the high bytes: text/data/bss share a low base, the heap sits above them, and
the stack is *way* up high (`0x16b…` here) growing downward — so heap and stack grow
toward each other across a vast unused gap. Run it again and every number changes:

```
=== ASLR ===
  the kernel randomizes the base of each region every exec...
```

That's **Address Space Layout Randomization** — it makes an attacker's "jump to this
fixed address" exploits unreliable. The page size is the other constant worth noting:

```
  getpagesize() = 16384 bytes
```

16 KB on Apple Silicon (4 KB on x86-64). Virtual memory is handed out a **page** at a
time, never a byte — the fact the whole rest of the module rests on.

## 2. `mmap` — mapping memory and files

`malloc` gives you bytes; `mmap` gives you whole pages wired straight into your
address space by the kernel. [`02_mmap.c`](02_mmap.c) (`make run2`) shows both uses.
First an **anonymous** mapping — raw zeroed pages, the very thing `malloc` itself
requests from the OS:

```
=== mmap: one page of anonymous memory ===
  mapped 16384 bytes at 0x102f4c000 (kernel chose the address)
  first byte before writing = 0 (anonymous pages start zeroed)
  wrote + read back: "hello from an anonymous mapping"
```

Then a **file** mapping, where the file's bytes *appear as memory* — a store to the
mapping is a write to the file, no `write()` call involved:

```
=== mmap: a file mapped into memory ===
  wrote 39 bytes to /tmp/m35_mmap_demo.txt via the mapping (no write() call).
  read it back with read(): "mmap wrote this straight into the file"
```

The conceptual payoff is **demand paging**: `mmap` reserves the address range
instantly, but a physical page is only allocated the first time you *touch* it — a
page fault traps to the kernel, which maps a page and re-runs your instruction. You
can map a file far larger than RAM and pay only for the pages you actually read.

## 3. Heap fragmentation

The heap is finite address space carved into blocks. Free blocks in an *interleaved*
pattern and the free space scatters into many non-contiguous holes.
[`03_fragmentation.c`](03_fragmentation.c) (`make run3`) allocates 16 blocks then
frees every other one:

```
=== Free every other block (interleaved frees) ===
  freed 8 blocks = 32768 bytes, but in 8 separate holes of 4096 bytes each
  layout (X=live . =hole): .X.X.X.X.X.X.X.X
```

Half the bytes are now free — but in eight separate 4096-byte holes. A request for
one big contiguous block can't reuse them and must come from elsewhere:

```
  total freed bytes = 32768, but the biggest single hole = 4096
  malloc(32768) succeeded (it had to grow the heap / use a fresh region)
  malloc(4096) (fits one hole) succeeded
```

This is **external fragmentation**: free space that's necessary but not *sufficient*,
because it isn't contiguous. (We stay honest here — we don't claim to read the system
allocator's internals, only what it can demonstrably do.) Real allocators fight this
with size classes, arenas, and **coalescing** — which you build next.

## 4. `my_malloc` — writing your own allocator

This is the Malloc-Lab idea, simplified and native: [`04_my_malloc.c`](04_my_malloc.c)
(`make run4`) manages one fixed byte array. Each block starts with a **header**
(payload size + a free flag); blocks sit back-to-back, so "the next block" is just
header + size away. `my_malloc` does a **first-fit** search and **splits** an
oversized free block; `my_free` marks the block free and **coalesces** it forward
with adjacent free neighbours.

```
=== A 1024-byte heap, header = 16 bytes ===
  empty:                [1008 free]   (1 blocks, 0 used, 1008 free)

=== Three allocations ===
  a=0x102a48014 b=0x102a4808c c=0x102a48164 (distinct, usable regions)
  wrote: "block A" "block B" "block C"
  after 3 mallocs:      [104 USED][200 USED][56 USED][600 free]   (4 blocks, 360 used, 600 free)
```

Three distinct, independently writable regions — a real allocator. Free the middle
block and a hole opens; free its neighbours and the holes **merge**:

```
=== Free the middle block (leaves a hole) ===
  after free(b):        [104 USED][200 free][56 USED][600 free]   (4 blocks, 160 used, 800 free)

=== Free its neighbours -> coalescing ===
  after free(c):        [104 USED][200 free][672 free]   (3 blocks, 104 used, 872 free)
  after free(a):        [1008 free]   (1 blocks, 0 used, 1008 free)
  the holes merged forward into one big free block.
```

The heap is back to a single free block, so a large request succeeds again:

```
=== Reuse the coalesced space ===
  my_malloc(300) succeeded at 0x102a48014
  after malloc(300):    [304 USED][688 free]   (2 blocks, 304 used, 688 free)
```

(Sizes round up to 8 for alignment, so 300 shows as a 304-byte payload.) That's the
whole game: headers + a free list + first-fit + split + coalesce.

---

## 5. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`.

### Exercise 35.1 — Add coalescing  (`make ex1`)
The allocator in [`exercises/ex1_coalesce.c`](exercises/ex1_coalesce.c) never merges
adjacent free blocks. As shipped, freeing all three blocks leaves four separate holes
and a 300-byte request **fails** even though 576 bytes are free:
```
  after free(a):        [104 free][200 free][56 free][216 free]   (4 blocks, 0 used, 576 free)
  my_malloc(300) FAILED (needs coalescing!)
```
Implement the forward-coalesce loop in `my_free`. Then `make sol1` shows the holes
merging into one block and the request succeeding:
```
  after free(a):        [624 free]   (1 blocks, 0 used, 624 free)
  my_malloc(300) succeeded
```

### Exercise 35.2 — `my_calloc` / `my_realloc`  (`make ex2`)
On top of a complete allocator, implement the two cousins in
[`exercises/ex2_calloc_realloc.c`](exercises/ex2_calloc_realloc.c): `my_calloc`
(overflow-checked, zeroed) and `my_realloc` (handles `NULL`/`0`, copies the smaller
of old/new size). The asserts must pass:
```
  my_calloc(8, 4): 32 zeroed bytes at 0x1022fc014
  my_realloc grew the block and kept "1234567"
  OK — all assertions passed.
```

### Exercise 35.3 — Count newlines via `mmap`  (`make ex3`)
In [`exercises/ex3_mmap_count.c`](exercises/ex3_mmap_count.c), `mmap` the provided
temp file read-only and count `'\n'` bytes by scanning the mapping like a char array
— no `read()`. Expected (`make sol3`):
```
  bytes = 34, lines = 3
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **Address space regions** | text/data/bss/heap/stack each have a home and a growth direction — the map every debugger and crash dump assumes |
| **ASLR** | Randomized bases per exec break fixed-address exploits; also why your printed addresses never repeat |
| **`mmap` + demand paging** | Pages, not bytes, are the unit; files and anonymous memory map into the same space, loaded lazily on first touch |
| **Fragmentation** | Free space must be *contiguous* to be usable — explains "out of memory" with bytes to spare |
| **Building `malloc`** | Headers + free list + first-fit + split + coalesce is the whole core; demystifies the allocator you use daily |

## Further reading

- **CS:APP3e, Chapter 9 — Virtual Memory** (address translation, paging, and the
  allocator design this module mirrors): http://csapp.cs.cmu.edu/
- **CS:APP Malloc Lab** (the canonical "write your own `malloc`" assignment — the
  natural next step after demo 4 and the exercises here):
  http://csapp.cs.cmu.edu/
- **OSTEP — Virtual Memory chapters** (Remzi & Andrea Arpaci-Dusseau; address spaces,
  paging, TLBs, swapping, in plain language): https://pages.cs.wisc.edu/~remzi/OSTEP/
- **MIT 6.1800 (Computer Systems)** (the systems course this part of the track
  follows): https://web.mit.edu/6.1800/

**Next:** Module 36 — Operating Systems with xv6 — read and extend a real Unix-like
kernel: syscalls, the scheduler, and the page tables that implement everything you
just saw from user space (C, RISC-V). See [../36_xv6_os/README.md](../36_xv6_os/README.md).
