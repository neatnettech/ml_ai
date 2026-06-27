# Module 44 — C++ for Systems  (OPTIONAL capstone of the CS Foundations track)
#
# Targets:
#   make            build all demos + exercises
#   make run        build and run all five demos in order
#   make run1..run5 run a single demo
#   make ex1..ex3   build and run YOUR exercise attempt (exercises/)
#   make sol1..sol3 build and run the reference solution (solutions/)
#   make clean      remove built binaries
#
# This module is C++ (not C): everything compiles with clang++ -std=c++17 and runs
# natively on Apple Silicon (arm64), Linux, or any host with a C++17 compiler.

CXX      := clang++
CXXFLAGS := -std=c++17 -Wall -Wextra -Wpedantic -g
BIN      := bin

DEMOS   := 01_references_raii 02_smart_pointers 03_templates 04_stl 05_vector_cpp
EXNAMES := ex1_raii_buffer ex2_clamp ex3_stl_rewrite
SOLS    := $(EXNAMES)

DEMO_BINS := $(addprefix $(BIN)/,$(DEMOS))
EX_BINS   := $(addprefix $(BIN)/ex_,$(EXNAMES))
SOL_BINS  := $(addprefix $(BIN)/sol_,$(SOLS))

.PHONY: all run clean run1 run2 run3 run4 run5 ex1 ex2 ex3 sol1 sol2 sol3

all: $(DEMO_BINS) $(EX_BINS) $(SOL_BINS)

$(BIN):
	mkdir -p $(BIN)

# Demos: bin/NAME from NAME.cpp
$(BIN)/%: %.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

# Exercises: bin/ex_NAME from exercises/NAME.cpp
$(BIN)/ex_%: exercises/%.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

# Solutions: bin/sol_NAME from solutions/NAME.cpp
$(BIN)/sol_%: solutions/%.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) -o $@ $<

run: run1 run2 run3 run4 run5

run1: $(BIN)/01_references_raii ; @echo "── demo 1 ──"; ./$<
run2: $(BIN)/02_smart_pointers ; @echo "── demo 2 ──"; ./$<
run3: $(BIN)/03_templates ; @echo "── demo 3 ──"; ./$<
run4: $(BIN)/04_stl ; @echo "── demo 4 ──"; ./$<
run5: $(BIN)/05_vector_cpp ; @echo "── demo 5 ──"; ./$<

ex1: $(BIN)/ex_ex1_raii_buffer ; ./$<
ex2: $(BIN)/ex_ex2_clamp ; ./$<
ex3: $(BIN)/ex_ex3_stl_rewrite ; ./$<

sol1: $(BIN)/sol_ex1_raii_buffer ; ./$<
sol2: $(BIN)/sol_ex2_clamp ; ./$<
sol3: $(BIN)/sol_ex3_stl_rewrite ; ./$<

clean:
	rm -rf $(BIN)
