# Module 41 — Networking Deep-Dive (native C sockets, loopback)
#
# Targets:
#   make            build all demos + exercises
#   make run        build and run all four demos in order
#   make run1..run4 run a single demo
#   make ex1..ex3   build and run YOUR exercise attempt (exercises/)
#   make sol1..sol3 build and run the reference solution (solutions/)
#   make clean      remove built binaries
#
# Portable C11 + the BSD sockets API. Everything talks to 127.0.0.1 on an OS-assigned
# ephemeral port and fork()s its own client + server, so each program is self-contained
# (no second terminal, no external network). Demo 4 uses pthreads, hence -pthread.

CC      := clang
CFLAGS  := -std=c11 -Wall -Wextra -Wpedantic -g
PTHREAD := -pthread
BIN     := bin

DEMOS   := 01_tcp_echo 02_udp 03_protocol 04_concurrent_server
EXNAMES := ex1_protocol_client ex2_new_command ex3_accept_loop
SOLS    := $(EXNAMES)

DEMO_BINS := $(addprefix $(BIN)/,$(DEMOS))
EX_BINS   := $(addprefix $(BIN)/ex_,$(EXNAMES))
SOL_BINS  := $(addprefix $(BIN)/sol_,$(SOLS))

.PHONY: all run clean run1 run2 run3 run4 ex1 ex2 ex3 sol1 sol2 sol3

all: $(DEMO_BINS) $(EX_BINS) $(SOL_BINS)

$(BIN):
	mkdir -p $(BIN)

# Demos: bin/NAME from NAME.c. Demo 4 needs pthreads.
$(BIN)/04_concurrent_server: 04_concurrent_server.c | $(BIN)
	$(CC) $(CFLAGS) $(PTHREAD) -o $@ $<

$(BIN)/%: %.c | $(BIN)
	$(CC) $(CFLAGS) -o $@ $<

# Exercises: bin/ex_NAME from exercises/NAME.c
$(BIN)/ex_%: exercises/%.c | $(BIN)
	$(CC) $(CFLAGS) -o $@ $<

# Solutions: bin/sol_NAME from solutions/NAME.c
$(BIN)/sol_%: solutions/%.c | $(BIN)
	$(CC) $(CFLAGS) -o $@ $<

run: run1 run2 run3 run4

run1: $(BIN)/01_tcp_echo ; @echo "── demo 1 ──"; ./$<
run2: $(BIN)/02_udp ; @echo "── demo 2 ──"; ./$<
run3: $(BIN)/03_protocol ; @echo "── demo 3 ──"; ./$<
run4: $(BIN)/04_concurrent_server ; @echo "── demo 4 ──"; ./$<

ex1: $(BIN)/ex_ex1_protocol_client ; ./$<
ex2: $(BIN)/ex_ex2_new_command ; ./$<
ex3: $(BIN)/ex_ex3_accept_loop ; ./$<

sol1: $(BIN)/sol_ex1_protocol_client ; ./$<
sol2: $(BIN)/sol_ex2_new_command ; ./$<
sol3: $(BIN)/sol_ex3_accept_loop ; ./$<

clean:
	rm -rf $(BIN)
