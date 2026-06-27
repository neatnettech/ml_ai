# Module 39 — Advanced Algorithms
#
# Targets:
#   make            build all demos + exercises + solutions
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

DEMOS   := 01_divide_conquer 02_greedy 03_shortest_paths 04_mst 05_max_flow 06_np_hardness
EXNAMES := ex1_union_find ex2_dijkstra ex3_vertex_cover
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

run1: $(BIN)/01_divide_conquer ; @echo "── demo 1 ──"; ./$<
run2: $(BIN)/02_greedy ; @echo "── demo 2 ──"; ./$<
run3: $(BIN)/03_shortest_paths ; @echo "── demo 3 ──"; ./$<
run4: $(BIN)/04_mst ; @echo "── demo 4 ──"; ./$<
run5: $(BIN)/05_max_flow ; @echo "── demo 5 ──"; ./$<
run6: $(BIN)/06_np_hardness ; @echo "── demo 6 ──"; ./$<

ex1: $(BIN)/ex_ex1_union_find ; ./$<
ex2: $(BIN)/ex_ex2_dijkstra ; ./$<
ex3: $(BIN)/ex_ex3_vertex_cover ; ./$<

sol1: $(BIN)/sol_ex1_union_find ; ./$<
sol2: $(BIN)/sol_ex2_dijkstra ; ./$<
sol3: $(BIN)/sol_ex3_vertex_cover ; ./$<

clean:
	rm -rf $(BIN)
