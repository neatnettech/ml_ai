# Module 47 — C & C++ From Zero  (standalone beginner on-ramp)
#
# Mixes C and C++: .c files build with clang -std=c11, .cpp with clang++ -std=c++17.
#
# Targets:
#   make            build all demos + exercises + solutions
#   make run        build and run all six demos in order
#   make run1..run6 run a single demo
#   make ex1..ex3   build and run YOUR exercise attempt (exercises/)
#   make sol1..sol3 build and run the reference solution (solutions/)
#   make clean      remove built binaries
#
# Runs natively on Apple Silicon (arm64), Linux, or any host with clang/clang++.

CC       ?= clang
CXX      ?= clang++
CFLAGS   := -std=c11   -Wall -Wextra -Wpedantic -g
CXXFLAGS := -std=c++17 -Wall -Wextra -Wpedantic -g
BIN      := bin

DEMOS_C   := 01_hello 02_types_control 03_functions_arrays 04_pointers_structs
DEMOS_CPP := 05_hello_cpp 06_class_raii
EX_C      := ex1_temperature ex2_word_count
EX_CPP    := ex3_stack_class

DEMO_BINS := $(addprefix $(BIN)/,$(DEMOS_C) $(DEMOS_CPP))
EX_BINS   := $(addprefix $(BIN)/ex_,$(EX_C) $(EX_CPP))
SOL_BINS  := $(addprefix $(BIN)/sol_,$(EX_C) $(EX_CPP))

.PHONY: all run clean run1 run2 run3 run4 run5 run6 \
        ex1 ex2 ex3 sol1 sol2 sol3

all: $(DEMO_BINS) $(EX_BINS) $(SOL_BINS)

$(BIN):
	mkdir -p $(BIN)

# --- Demos: two pattern rules, keyed by extension ---
$(BIN)/%: %.c   | $(BIN)
	$(CC)  $(CFLAGS)   -o $@ $<
$(BIN)/%: %.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

# --- Exercises: bin/ex_NAME from exercises/NAME.{c,cpp} ---
$(BIN)/ex_%: exercises/%.c   | $(BIN)
	$(CC)  $(CFLAGS)   -o $@ $<
$(BIN)/ex_%: exercises/%.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

# --- Solutions: bin/sol_NAME from solutions/NAME.{c,cpp} ---
$(BIN)/sol_%: solutions/%.c   | $(BIN)
	$(CC)  $(CFLAGS)   -o $@ $<
$(BIN)/sol_%: solutions/%.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

run: run1 run2 run3 run4 run5 run6
run1: $(BIN)/01_hello            ; @echo "── demo 1 ──"; ./$<
run2: $(BIN)/02_types_control    ; @echo "── demo 2 ──"; ./$<
run3: $(BIN)/03_functions_arrays ; @echo "── demo 3 ──"; ./$<
run4: $(BIN)/04_pointers_structs ; @echo "── demo 4 ──"; ./$<
run5: $(BIN)/05_hello_cpp        ; @echo "── demo 5 ──"; ./$<
run6: $(BIN)/06_class_raii       ; @echo "── demo 6 ──"; ./$<

ex1: $(BIN)/ex_ex1_temperature ; ./$<
ex2: $(BIN)/ex_ex2_word_count  ; ./$<
ex3: $(BIN)/ex_ex3_stack_class ; ./$<

sol1: $(BIN)/sol_ex1_temperature ; ./$<
sol2: $(BIN)/sol_ex2_word_count  ; ./$<
sol3: $(BIN)/sol_ex3_stack_class ; ./$<

clean:
	rm -rf $(BIN)
