# Module 36 — Operating Systems with xv6
#
# Targets (PART A — native POSIX demos, run on this Mac):
#   make            build all demos + exercises + solutions
#   make run        build and run all four demos in order
#   make run1..run4 run a single demo (run4 = tiny shell in demo mode)
#   make ex1 ex2    build and run YOUR exercise attempt (exercises/)
#   make sol1 sol2  build and run the reference solution (solutions/)
#   make help-xv6   print the PART B (xv6 in qemu) setup pointer
#   make clean      remove built binaries
#
# Exercise 36.3 is xv6/RISC-V-gated (qemu + RISC-V toolchain) — it is a guided
# markdown write-up (exercises/ex3_add_syscall.md), so there is no make target for it.
#
# PART A is portable C11 — runs natively on Apple Silicon (arm64), Linux, or the
# x86-64 setup/ container. _DARWIN_C_SOURCE exposes the POSIX prototypes on macOS.

CC      := clang
CFLAGS  := -std=c11 -Wall -Wextra -Wpedantic -g
BIN     := bin

DEMOS   := 01_fork_exec 02_pipes 03_syscalls 04_shell
EXNAMES := ex1_pipe_shell ex2_run_status
SOLS    := $(EXNAMES)

DEMO_BINS := $(addprefix $(BIN)/,$(DEMOS))
EX_BINS   := $(addprefix $(BIN)/ex_,$(EXNAMES))
SOL_BINS  := $(addprefix $(BIN)/sol_,$(SOLS))

.PHONY: all run clean run1 run2 run3 run4 ex1 ex2 sol1 sol2 help-xv6

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

run1: $(BIN)/01_fork_exec ; @echo "── demo 1 ──"; ./$<
run2: $(BIN)/02_pipes ; @echo "── demo 2 ──"; ./$<
run3: $(BIN)/03_syscalls ; @echo "── demo 3 ──"; ./$<
run4: $(BIN)/04_shell ; @echo "── demo 4 (tiny shell, demo mode) ──"; ./$< --demo

ex1: $(BIN)/ex_ex1_pipe_shell ; ./$<
ex2: $(BIN)/ex_ex2_run_status ; ./$<

sol1: $(BIN)/sol_ex1_pipe_shell ; ./$<
sol2: $(BIN)/sol_ex2_run_status ; ./$<

help-xv6:
	@echo "PART B (xv6) runs under qemu-system-riscv64, NOT natively here. Steps:"
	@echo "  brew install qemu                                  # qemu is in setup/Brewfile"
	@echo "  # install the RISC-V toolchain (riscv64-unknown-elf-gcc) — see README PART B"
	@echo "  git clone https://github.com/mit-pdos/xv6-riscv.git"
	@echo "  cd xv6-riscv && make qemu      # boot xv6; exit with Ctrl-a x"
	@echo "Labs/book: https://pdos.csail.mit.edu/6.1810/2024/xv6.html"
	@echo "Exercise 36.3 (add a syscall) is guided in exercises/ex3_add_syscall.md"

clean:
	rm -rf $(BIN)
