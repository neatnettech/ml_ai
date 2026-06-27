# Module 38 — Algorithms & Data Structures
#
# Targets:
#   make            build all demos + exercises
#   make run        build and run all six demos in order
#   make run1..run6 run a single demo
#   make ex1..ex3   build and run YOUR exercise attempt (exercises/)
#   make sol1..sol3 build and run the reference solution (solutions/)
#   make clean      remove built binaries
#
# Everything here is portable C11 — runs natively on Apple Silicon (arm64), Linux,
# or inside the x86-64 setup/ container. No architecture-specific code in this module.

CC      := clang
CFLAGS  := -std=c11 -Wall -Wextra -Wpedantic -g -O2
BIN     := bin

DEMOS   := 01_sorting 02_searching 03_hash_table 04_trees_heaps 05_graphs 06_dynamic_programming
EXNAMES := ex1_quicksort ex2_hash_set ex3_edit_distance
SOLS    := $(EXNAMES)

DEMO_BINS := $(addprefix $(BIN)/,$(DEMOS))
EX_BINS   := $(addprefix $(BIN)/ex_,$(EXNAMES))
SOL_BINS  := $(addprefix $(BIN)/sol_,$(SOLS))

.PHONY: all run clean run1 run2 run3 run4 run5 run6 ex1 ex2 ex3 sol1 sol2 sol3

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

run: run1 run2 run3 run4 run5 run6

run1: $(BIN)/01_sorting ; @echo "── demo 1 ──"; ./$<
run2: $(BIN)/02_searching ; @echo "── demo 2 ──"; ./$<
run3: $(BIN)/03_hash_table ; @echo "── demo 3 ──"; ./$<
run4: $(BIN)/04_trees_heaps ; @echo "── demo 4 ──"; ./$<
run5: $(BIN)/05_graphs ; @echo "── demo 5 ──"; ./$<
run6: $(BIN)/06_dynamic_programming ; @echo "── demo 6 ──"; ./$<

ex1: $(BIN)/ex_ex1_quicksort ; ./$<
ex2: $(BIN)/ex_ex2_hash_set ; ./$<
ex3: $(BIN)/ex_ex3_edit_distance ; ./$<

sol1: $(BIN)/sol_ex1_quicksort ; ./$<
sol2: $(BIN)/sol_ex2_hash_set ; ./$<
sol3: $(BIN)/sol_ex3_edit_distance ; ./$<

clean:
	rm -rf $(BIN)
