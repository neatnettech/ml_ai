# Module 43 — Security & Cryptography Foundations
#
# Targets:
#   make            build all demos + exercises
#   make run        build and run all four demos in order
#   make run1..run4 run a single demo
#   make ex1..ex3   build and run YOUR exercise attempt (exercises/)
#   make sol1..sol3 build and run the reference solution (solutions/)
#   make clean      remove built binaries
#
# Everything here is portable C11 — runs natively on Apple Silicon (arm64), Linux,
# or inside the x86-64 setup/ container. The vulnerable demos are written to compile
# warning-clean AND run safely: they illustrate the root cause without hijacking
# control flow or crashing the process (see README.md).

CC      := clang
CFLAGS  := -std=c11 -Wall -Wextra -Wpedantic -g
BIN     := bin

DEMOS   := 01_buffer_overflow 02_format_string 03_integer_overflow 04_crypto_primitives
EXNAMES := ex1_copy_name ex2_constant_time_eq ex3_checked_alloc_size
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

run1: $(BIN)/01_buffer_overflow ; @echo "── demo 1 ──"; ./$<
run2: $(BIN)/02_format_string ; @echo "── demo 2 ──"; ./$<
run3: $(BIN)/03_integer_overflow ; @echo "── demo 3 ──"; ./$<
run4: $(BIN)/04_crypto_primitives ; @echo "── demo 4 ──"; ./$<

ex1: $(BIN)/ex_ex1_copy_name ; ./$<
ex2: $(BIN)/ex_ex2_constant_time_eq ; ./$<
ex3: $(BIN)/ex_ex3_checked_alloc_size ; ./$<

sol1: $(BIN)/sol_ex1_copy_name ; ./$<
sol2: $(BIN)/sol_ex2_constant_time_eq ; ./$<
sol3: $(BIN)/sol_ex3_checked_alloc_size ; ./$<

clean:
	rm -rf $(BIN)
