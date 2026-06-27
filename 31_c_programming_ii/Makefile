# Module 31 — C Programming II
#
# Targets:
#   make             build all demos + exercises + solutions
#   make run         build and run all five demos in order
#   make run1..run5  run a single demo
#   make run3-debug  run demo 3 built with -DDEBUG (conditional compilation)
#   make ex1..ex3    build and run YOUR exercise attempt (exercises/)
#   make sol1..sol3  build and run the reference solution (solutions/)
#   make clean       remove built binaries
#
# Everything here builds & runs NATIVELY with clang on Apple Silicon (arm64).
# valgrind/gdb are NOT used by any target (valgrind is Linux-only) — those live in
# the x86-64 container from Module 28's setup/. lldb is the native macOS debugger.

CC      := clang
CFLAGS  := -std=c11 -Wall -Wextra -Wpedantic -g
BIN     := bin

# Single-file demos compiled the simple way (one .c -> one binary).
SIMPLE_DEMOS := 02_function_pointers 03_preprocessor 04_undefined_behavior 05_debugging
EXNAMES      := ex1_lcm ex2_find ex3_min_macro
SOLS         := $(EXNAMES)

SIMPLE_BINS := $(addprefix $(BIN)/,$(SIMPLE_DEMOS))
EX_BINS     := $(addprefix $(BIN)/ex_,$(EXNAMES))
SOL_BINS    := $(addprefix $(BIN)/sol_,$(SOLS))

.PHONY: all run clean run1 run2 run3 run3-debug run4 run5 \
        ex1 ex2 ex3 sol1 sol2 sol3

all: $(BIN)/01_multifile $(SIMPLE_BINS) $(EX_BINS) $(SOL_BINS)

$(BIN):
	mkdir -p $(BIN)

# ---- Demo 1: the MULTI-FILE build (separate compilation -> linking) ------------
# Compile each translation unit to its own object file, then LINK them together.
# This is the whole teaching point: mathlib.o has the definitions, the main has the
# calls, and the linker resolves one against the other.
$(BIN)/mathlib.o: mathlib.c mathlib.h | $(BIN)
	$(CC) $(CFLAGS) -c mathlib.c -o $@

$(BIN)/01_multifile_main.o: 01_multifile_main.c mathlib.h | $(BIN)
	$(CC) $(CFLAGS) -c 01_multifile_main.c -o $@

$(BIN)/01_multifile: $(BIN)/mathlib.o $(BIN)/01_multifile_main.o
	$(CC) $(CFLAGS) $^ -o $@

# ---- Single-file demos: bin/NAME from NAME.c -----------------------------------
$(BIN)/%: %.c | $(BIN)
	$(CC) $(CFLAGS) -o $@ $<

# ---- Exercises ----------------------------------------------------------------
# ex1 / sol1 link against mathlib.c (multi-file edit loop); the others are single.
$(BIN)/ex_ex1_lcm: exercises/ex1_lcm.c mathlib.c mathlib.h | $(BIN)
	$(CC) $(CFLAGS) exercises/ex1_lcm.c mathlib.c -o $@
$(BIN)/sol_ex1_lcm: solutions/ex1_lcm.c mathlib.c mathlib.h | $(BIN)
	$(CC) $(CFLAGS) solutions/ex1_lcm.c mathlib.c -o $@

$(BIN)/ex_%: exercises/%.c | $(BIN)
	$(CC) $(CFLAGS) -o $@ $<
$(BIN)/sol_%: solutions/%.c | $(BIN)
	$(CC) $(CFLAGS) -o $@ $<

# ---- Run targets ---------------------------------------------------------------
run: run1 run2 run3 run4 run5

run1: $(BIN)/01_multifile ; @echo "── demo 1: multi-file ──"; ./$<
run2: $(BIN)/02_function_pointers ; @echo "── demo 2: function pointers ──"; ./$<
run3: $(BIN)/03_preprocessor ; @echo "── demo 3: preprocessor ──"; ./$<
run4: $(BIN)/04_undefined_behavior ; @echo "── demo 4: undefined behavior ──"; ./$<
run5: $(BIN)/05_debugging ; @echo "── demo 5: debugging ──"; ./$<

# Demo 3 built with -DDEBUG to show conditional compilation (#ifdef DEBUG).
run3-debug: | $(BIN)
	$(CC) $(CFLAGS) -DDEBUG -o $(BIN)/03_preprocessor_debug 03_preprocessor.c
	@echo "── demo 3: preprocessor (-DDEBUG) ──"; ./$(BIN)/03_preprocessor_debug

ex1: $(BIN)/ex_ex1_lcm ; ./$<
ex2: $(BIN)/ex_ex2_find ; ./$<
ex3: $(BIN)/ex_ex3_min_macro ; ./$<

sol1: $(BIN)/sol_ex1_lcm ; ./$<
sol2: $(BIN)/sol_ex2_find ; ./$<
sol3: $(BIN)/sol_ex3_min_macro ; ./$<

clean:
	rm -rf $(BIN)
