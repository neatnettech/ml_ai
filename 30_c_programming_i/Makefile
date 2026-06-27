# Module 30 — C Programming I: the memory model & pointers
#
# Targets:
#   make            build all demos + exercises
#   make run        build and run all five demos in order
#   make run1..run5 run a single demo
#   make ex1..ex3   build and run YOUR exercise attempt (exercises/)
#   make sol1..sol3 build and run the reference solution (solutions/)
#   make clean      remove built binaries
#
# Everything here is portable C11 — runs natively on Apple Silicon (arm64), Linux,
# or inside the x86-64 setup/ container. No architecture-specific code in this module.

CC      := clang
CFLAGS  := -std=c11 -Wall -Wextra -Wpedantic -g
BIN     := bin

DEMOS   := 01_pointers 02_stack_heap 03_strings 04_structs 05_dynamic_array
EXNAMES := ex1_strrev ex2_linked_list ex3_vec_ops
SOLS    := $(EXNAMES)

DEMO_BINS := $(addprefix $(BIN)/,$(DEMOS))
EX_BINS   := $(addprefix $(BIN)/ex_,$(EXNAMES))
SOL_BINS  := $(addprefix $(BIN)/sol_,$(SOLS))

.PHONY: all run clean run1 run2 run3 run4 run5 ex1 ex2 ex3 sol1 sol2 sol3

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

run: run1 run2 run3 run4 run5

run1: $(BIN)/01_pointers ; @echo "── demo 1 ──"; ./$<
run2: $(BIN)/02_stack_heap ; @echo "── demo 2 ──"; ./$<
run3: $(BIN)/03_strings ; @echo "── demo 3 ──"; ./$<
run4: $(BIN)/04_structs ; @echo "── demo 4 ──"; ./$<
run5: $(BIN)/05_dynamic_array ; @echo "── demo 5 ──"; ./$<

ex1: $(BIN)/ex_ex1_strrev ; ./$<
ex2: $(BIN)/ex_ex2_linked_list ; ./$<
ex3: $(BIN)/ex_ex3_vec_ops ; ./$<

sol1: $(BIN)/sol_ex1_strrev ; ./$<
sol2: $(BIN)/sol_ex2_linked_list ; ./$<
sol3: $(BIN)/sol_ex3_vec_ops ; ./$<

clean:
	rm -rf $(BIN)
