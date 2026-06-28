# Track 6 — CS Foundations (from bits to systems)

> **Status:** ✅ all 17 modules built (28–44). Each is real source + a lab README in
> the repo's Purpose / Prerequisites / What-you-learned / Further-reading / Next
> convention. Everything builds warning-free (`-Wall -Wextra -Wpedantic`); the native
> parts run on Apple Silicon, with x86-64 (CS:APP bomb/attack labs) and RISC-V (xv6)
> parts documented for the `setup/` container + qemu.

## Why this track

The existing catalog (1–27) teaches ML, generative vision, backend, security, and
agents — all on top of Python and high-level libraries. This track goes the other
direction: **down to the metal and back up**. Single bits → number representation →
logic gates → a CPU → C and pointers → assembly → caches → the operating system →
algorithms → compilers → distributed systems → security theory. The goal is the
mental model an MIT EECS grad has: knowing what *actually happens* when code runs.

It can be taken **first** (it's foundational) despite the high module numbers — the
numbering just appends to the catalog. Where it overlaps existing tracks it
*deepens* rather than repeats: algorithms feed the [Pure ML track](README.md),
networking/security connect to the [White-Hat track](21_networking_and_packets/),
and the crypto theory sits under your applied [Module 18](18_cryptography/).

## Decisions (locked)

- **Depth:** full systems core (~14 core + 3 optional-depth modules).
- **Language:** **C-first** through the systems core; one **optional C++** module at the end.
- **Format:** real `.c` / `.s` source + `Makefile` + a `README.md` lab per module
  (exercises with `// TODO` + solutions). **No jupyter** — systems work needs a real
  toolchain, not notebooks.
- **Backbone:** build the repo's own labs; point **Further reading** at the canonical
  spine — **CS:APP3e** (primary text + its self-study labs), **Nand2Tetris** (the
  logic→CPU build), **MIT OCW** (lectures + psets), **xv6** (the OS).

## The path

Phases build strictly on each other. Optional-depth modules can be skipped on a
first pass without breaking the chain.

### Phase A — The machine (bits → CPU)

| # | Module | You build (in) | Spine / MIT |
|---|--------|----------------|-------------|
| 28 | **Bits, Bytes & Number Representation** | bit-pattern printers, two's-complement & IEEE-754 explorers, bitwise tricks (C) | CS:APP ch.2 + Data Lab; MIT 6.191 |
| 29 | **Digital Logic & the CPU** | NAND → gates → mux → ALU → registers → a tiny CPU + machine code (HDL + a C gate-sim) | Nand2Tetris proj 1–5; MIT 6.191/6.004 |

### Phase B — C and the bare machine

| # | Module | You build (in) | Spine / MIT |
|---|--------|----------------|-------------|
| 30 | **C Programming I** | memory model, pointers, stack vs heap; a dynamic array + linked list (C) | K&R; CS:APP ch.3 intro |
| 31 | **C Programming II** | multi-file builds, Makefiles, `gdb`/`valgrind`, function pointers, the preprocessor, UB (C) | K&R; Beej's C guide |
| 32 | **Assembly & the ISA** | read `gcc -S`/`objdump`, registers, calling convention, stack frames; defuse a binary bomb (C + asm) | CS:APP ch.3 + Bomb/Attack Lab; MIT 6.191 |
| 33 | **Computer Architecture** | pipelining & hazards, the memory hierarchy, cache-timing experiments, locality (C) | CS:APP ch.5–6 + Cache Lab; MIT 6.191 |

### Phase C — The operating system

| # | Module | You build (in) | Spine / MIT |
|---|--------|----------------|-------------|
| 34 | **Linking, Loading & Processes** | the compile→link→load pipeline, ELF, static/dynamic libs, processes, signals; a tiny shell (C) | CS:APP ch.7–8 + Shell Lab; MIT 6.1800 |
| 35 | **Virtual Memory & Allocation** | address translation, paging, `mmap`; write your own `malloc`/`free` (C) | CS:APP ch.9 + Malloc Lab; MIT 6.1800 |
| 36 | **Operating Systems with xv6** | read & extend a real Unix-like kernel: syscalls, scheduler, page tables (C, RISC-V) | xv6 book + MIT 6.1810 labs |
| 37 | **Concurrency** | threads, mutexes, condition vars, races, deadlock, atomics (C / pthreads) | CS:APP ch.12; OSTEP; MIT 6.1810 |

### Phase D — Algorithms, languages, systems-at-scale

| # | Module | You build (in) | Spine / MIT |
|---|--------|----------------|-------------|
| 38 | **Algorithms & Data Structures** | asymptotics, sorting, hashing, trees/heaps, graphs, DP (C + Python — bridges to Pure ML) | CLRS; MIT 6.1210 (6.006) |
| 39 | **Advanced Algorithms** *(optional-depth)* | greedy/D&C proofs, network flow, NP-completeness, approximation | CLRS; MIT 6.1220 (6.046) |
| 40 | **Compilers & Language Engineering** | lexer → parser → AST → codegen; a small interpreter/compiler (C or Python) | Crafting Interpreters; Nand2Tetris 6–11; MIT 6.035 |
| 41 | **Networking Deep-Dive** | TCP/IP internals, routing, RPC (C; extends [Module 21](21_networking_and_packets/)) | Beej's Guide; MIT 6.1800 |
| 42 | **Distributed Systems** *(optional-depth)* | RPC, replication, consensus (Raft), fault tolerance | MIT 6.5840 (6.824) — *note: Go, a deliberate divergence* |

### Phase E — Security and (optional) C++

| # | Module | You build (in) | Spine / MIT |
|---|--------|----------------|-------------|
| 43 | **Security & Cryptography Foundations** | threat models, the classic memory-safety vulns (ties to [vulnlab](23_web_app_security/)), crypto primitives & protocol theory (under applied [Module 18](18_cryptography/)) | MIT 6.5660 (sys security), 6.1600 |
| 44 | **C++ for Systems** *(optional)* | RAII, references, templates, STL, smart pointers, move semantics; rewrite an earlier C lab in modern C++ | "A Tour of C++"; cppreference |
| 45 | **C/C++ ↔ Python (FFI & Extensions)** | the bridge back to the Python tracks: one Mandelbrot kernel called via ctypes, the CPython C-API, pybind11, and NumPy, benchmarked vs pure Python | Python C-API & ctypes docs; pybind11 |

## Toolchain & the Apple-Silicon catch

This machine is **arm64**, but the gold-standard labs assume **x86-64** (CS:APP's
bomb/attack/cache labs are x86-64 binaries) and **RISC-V** (xv6). Plan:

- **CS:APP labs (32–35):** run in an **x86-64 Linux container** (Docker, or UTM VM).
  Keeps the disassembly/ABI exactly as the book teaches. *(Recommended default.)*
  Alternative: do assembly natively in **ARM64** — cleaner ISA, but diverges from
  CS:APP's x86-64 text.
- **xv6 (36):** **qemu-system-riscv64** + the RISC-V GNU toolchain — cross-platform,
  no arch headache.
- **Logic (29):** the **Nand2Tetris** hardware simulator (Java) — OS-agnostic.
- **Local C work (28, 30–31, 37–38):** native `clang`/`make`; `lldb` (Mac) or `gdb`;
  `valgrind` is Linux-only → use the Docker box for leak-checking.

A `Brewfile` + a `Dockerfile` for the x86-64 lab box would be Module 28's setup
deliverable, so every later module has a consistent environment.

## Decisions made during the build

- **Assembly (Module 32):** taught x86-64 (CS:APP) as primary with the bomb/attack labs
  in the `setup/` x86-64 container; added a native **AArch64** demo that assembles and
  runs on this Mac so the module isn't all theory.
- **Module 42 (distributed):** re-cast the MIT 6.5840 (Go) concepts as deterministic
  in-process **C simulations** (RPC, Lamport/vector clocks, quorum replication, a
  Raft-lite election + log commit) — self-contained and reproducible.
- **xv6 (Module 36):** native POSIX demos (fork/exec, pipes, syscalls, a tiny shell)
  run here; the xv6 kernel labs are documented as a qemu/RISC-V guide (not run here).

## What's not done

- **Progress tracker / CI** across the whole catalog — still deferred (same as the ML
  tracks). A CI job that runs `make` in every `2x_`/`3x_`/`4x_` module would catch
  regressions cheaply.
- The **x86-64 container** (`28_bits_and_bytes/setup/`) and **qemu-riscv** are documented
  but their gated labs (CS:APP bomb/attack, xv6 kernel) haven't been run end-to-end here.
