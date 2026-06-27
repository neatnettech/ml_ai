# Module 33 — Computer Architecture (measured)
#
# Targets:
#   make            build all demos + exercises
#   make run        build and run all four demos in order
#   make run1..run4 run a single demo
#   make ex1..ex3   build and run YOUR exercise attempt (exercises/)
#   make sol1..sol3 build and run the reference solution (solutions/)
#   make clean      remove built binaries
#
# Portable C11 — runs natively on Apple Silicon (arm64), Linux, or the x86-64
# setup/ container. Built at -O2 so timings are realistic; the measured loops use
# `volatile` sinks so the optimizer can't delete the work we're timing.

CC      := clang
CFLAGS  := -std=c11 -Wall -Wextra -Wpedantic -g -O2
BIN     := bin

DEMOS   := 01_locality 02_stride 03_branch_prediction 04_memory_hierarchy
EXNAMES := ex1_cache_line ex2_branch_speedup ex3_matmul_order
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

run1: $(BIN)/01_locality ; @echo "── demo 1 ──"; ./$<
run2: $(BIN)/02_stride ; @echo "── demo 2 ──"; ./$<
run3: $(BIN)/03_branch_prediction ; @echo "── demo 3 ──"; ./$<
run4: $(BIN)/04_memory_hierarchy ; @echo "── demo 4 ──"; ./$<

ex1: $(BIN)/ex_ex1_cache_line ; ./$<
ex2: $(BIN)/ex_ex2_branch_speedup ; ./$<
ex3: $(BIN)/ex_ex3_matmul_order ; ./$<

sol1: $(BIN)/sol_ex1_cache_line ; ./$<
sol2: $(BIN)/sol_ex2_branch_speedup ; ./$<
sol3: $(BIN)/sol_ex3_matmul_order ; ./$<

clean:
	rm -rf $(BIN)
