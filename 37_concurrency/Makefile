# Module 37 — Concurrency
#
# Targets:
#   make            build all demos + exercises
#   make run        build and run all five demos in order
#   make run1..run5 run a single demo
#   make ex1..ex3   build and run YOUR exercise attempt (exercises/)
#   make sol1..sol3 build and run the reference solution (solutions/)
#   make clean      remove built binaries
#
# Portable C11 + POSIX threads — runs natively on Apple Silicon (arm64) or Linux.
# Threads need -pthread at BOTH compile and link time; it is in CFLAGS so the
# single-step `clang -o bin/x x.c` rule below covers both.

CC      := clang
CFLAGS  := -std=c11 -Wall -Wextra -Wpedantic -g -pthread
BIN     := bin

DEMOS   := 01_threads 02_race 03_mutex 04_condvar 05_atomics
EXNAMES := ex1_parallel_sum ex2_fix_race ex3_deadlock
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

run1: $(BIN)/01_threads ; @echo "── demo 1 ──"; ./$<
run2: $(BIN)/02_race ; @echo "── demo 2 ──"; ./$<
run3: $(BIN)/03_mutex ; @echo "── demo 3 ──"; ./$<
run4: $(BIN)/04_condvar ; @echo "── demo 4 ──"; ./$<
run5: $(BIN)/05_atomics ; @echo "── demo 5 ──"; ./$<

ex1: $(BIN)/ex_ex1_parallel_sum ; ./$<
ex2: $(BIN)/ex_ex2_fix_race ; ./$<
ex3: $(BIN)/ex_ex3_deadlock ; ./$<

sol1: $(BIN)/sol_ex1_parallel_sum ; ./$<
sol2: $(BIN)/sol_ex2_fix_race ; ./$<
sol3: $(BIN)/sol_ex3_deadlock ; ./$<

clean:
	rm -rf $(BIN)
