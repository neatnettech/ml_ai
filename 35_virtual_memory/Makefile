# Module 35 — Virtual Memory & Allocation
#
# Targets:
#   make            build all demos + exercises
#   make run        build and run all four demos in order
#   make run1..run4 run a single demo
#   make ex1..ex3   build and run YOUR exercise attempt (exercises/)
#   make sol1..sol3 build and run the reference solution (solutions/)
#   make clean      remove built binaries (and any stray temp files)
#
# Native C11 — runs natively on Apple Silicon (arm64) and Linux. The mmap demos use
# POSIX (mmap/munmap/getpagesize); on macOS we #define _DARWIN_C_SOURCE in-source.
# Temp files are created under /tmp and removed by the programs themselves.

CC      := clang
CFLAGS  := -std=c11 -Wall -Wextra -Wpedantic -g
BIN     := bin

DEMOS   := 01_address_space 02_mmap 03_fragmentation 04_my_malloc
EXNAMES := ex1_coalesce ex2_calloc_realloc ex3_mmap_count
SOLS    := $(EXNAMES)

DEMO_BINS := $(addprefix $(BIN)/,$(DEMOS))
EX_BINS   := $(addprefix $(BIN)/ex_,$(EXNAMES))
SOL_BINS  := $(addprefix $(BIN)/sol_,$(SOLS))

.PHONY: all run clean run1 run2 run3 run4 ex1 ex2 ex3 sol1 sol2 sol3

all: $(DEMO_BINS) $(EX_BINS) $(SOL_BINS)

$(BIN):
	mkdir -p $(BIN)

# Demos: bin/NAME from NAME.c
$(BIN)/%: %.c | $(BIN)
	$(CC) $(CFLAGS) -o $@ $<

# Exercises: bin/ex_NAME from exercises/NAME.c
$(BIN)/ex_%: exercises/%.c | $(BIN)
	$(CC) $(CFLAGS) -o $@ $<

# Solutions: bin/sol_NAME from solutions/NAME.c
$(BIN)/sol_%: solutions/%.c | $(BIN)
	$(CC) $(CFLAGS) -o $@ $<

run: run1 run2 run3 run4

run1: $(BIN)/01_address_space ; @echo "── demo 1 ──"; ./$<
run2: $(BIN)/02_mmap ; @echo "── demo 2 ──"; ./$<
run3: $(BIN)/03_fragmentation ; @echo "── demo 3 ──"; ./$<
run4: $(BIN)/04_my_malloc ; @echo "── demo 4 ──"; ./$<

ex1: $(BIN)/ex_ex1_coalesce ; ./$<
ex2: $(BIN)/ex_ex2_calloc_realloc ; ./$<
ex3: $(BIN)/ex_ex3_mmap_count ; ./$<

sol1: $(BIN)/sol_ex1_coalesce ; ./$<
sol2: $(BIN)/sol_ex2_calloc_realloc ; ./$<
sol3: $(BIN)/sol_ex3_mmap_count ; ./$<

clean:
	rm -rf $(BIN)
	rm -f /tmp/m35_mmap_demo.txt /tmp/m35_ex3_count.txt
