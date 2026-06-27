# Module 32 — Assembly & the ISA
#
# Targets:
#   make            build all native demos + exercises
#   make run        build and run the native demos in order
#   make run1       run demo 1 (factorial/loop C program)
#   make run2       assemble + link + run the hand-written arm64 add_asm
#   make run3       run demo 3 (calling-convention C program)
#   make asm1       emit native arm64 assembly for demo 1 -> 01_compile_down.s
#   make asm3       emit native arm64 assembly for demo 3 -> 03_calling_convention.s
#   make ex1        assemble + link + run YOUR arm64 max2 (exercises/)
#   make sol1       assemble + link + run the reference arm64 max2 (solutions/)
#   make clean      remove built binaries and generated .s
#
# The C and the AArch64 .s here build and run NATIVELY on Apple Silicon (arm64).
# The CS:APP Bomb/Attack labs are x86-64 and run in the setup/ container — see README.
# Exercises 32.2 and 32.3 are paper exercises (.md), no build target.

CC      := clang
CFLAGS  := -std=c11 -Wall -Wextra -Wpedantic -g
BIN     := bin

.PHONY: all run clean run1 run2 run3 asm1 asm3 ex1 sol1

all: $(BIN)/01_compile_down $(BIN)/02_add $(BIN)/03_calling_convention \
     $(BIN)/ex1_max2 $(BIN)/sol1_max2

$(BIN):
	mkdir -p $(BIN)

# Demo 1: plain C program
$(BIN)/01_compile_down: 01_compile_down.c | $(BIN)
	$(CC) $(CFLAGS) -o $@ $<

# Demo 2: C driver + hand-written arm64 assembly, linked together natively
$(BIN)/02_add: 02_add_main.c 02_add.s | $(BIN)
	$(CC) $(CFLAGS) -o $@ 02_add_main.c 02_add.s

# Demo 3: plain C program
$(BIN)/03_calling_convention: 03_calling_convention.c | $(BIN)
	$(CC) $(CFLAGS) -o $@ $<

# Exercise 1: your arm64 max2 + driver
$(BIN)/ex1_max2: exercises/ex1_max2_main.c exercises/ex1_max2.s | $(BIN)
	$(CC) $(CFLAGS) -o $@ exercises/ex1_max2_main.c exercises/ex1_max2.s

# Solution 1: reference arm64 max2 + driver
$(BIN)/sol1_max2: exercises/ex1_max2_main.c solutions/ex1_max2.s | $(BIN)
	$(CC) $(CFLAGS) -o $@ exercises/ex1_max2_main.c solutions/ex1_max2.s

run: run1 run2 run3

run1: $(BIN)/01_compile_down ; @echo "── demo 1: C → asm ──"; ./$<
run2: $(BIN)/02_add ; @echo "── demo 2: hand-written arm64 add_asm ──"; ./$<
run3: $(BIN)/03_calling_convention ; @echo "── demo 3: calling convention ──"; ./$<

# View the native arm64 assembly the compiler generates. -O1 keeps it readable.
# (In the x86-64 container, add -masm=intel and use gcc for CS:APP-style output.)
asm1: ; $(CC) -O1 -S 01_compile_down.c -o 01_compile_down.s ; @echo "wrote 01_compile_down.s"
asm3: ; $(CC) -O1 -S 03_calling_convention.c -o 03_calling_convention.s ; @echo "wrote 03_calling_convention.s"

ex1: $(BIN)/ex1_max2 ; ./$<
sol1: $(BIN)/sol1_max2 ; ./$<

clean:
	rm -rf $(BIN) 01_compile_down.s 03_calling_convention.s
