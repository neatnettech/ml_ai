# Module 34 — Linking, Loading & Processes
#
# Targets:
#   make            build all demos + exercises + libraries
#   make run        build and run all four demos in order
#   make run1..run4 run a single demo
#                     run1 = four build stages (-E/-S/-c/link) on hello.c
#                     run2 = link against a STATIC library (libmymath.a)
#                     run3 = link against a DYNAMIC library (libmymath.dylib)
#                     run4 = internal vs external linkage (two TUs)
#   make symbols    nm / otool inspection of the built binaries (helper)
#   make ex1..ex3   build and run YOUR exercise attempt (exercises/)
#                     (ex2 is EXPECTED TO FAIL until you fix it — that's the point)
#   make sol1..sol3 build and run the reference solution (solutions/)
#   make clean      remove bin/ (binaries, .o, .a, .dylib, stage artifacts)
#
# Toolchain note: native macOS uses Mach-O + dyld; tools are nm / otool / clang.
# The Linux/ELF equivalents (readelf, ldd, -shared, .so) are noted in the README.

CC      := clang
CFLAGS  := -std=c11 -Wall -Wextra -Wpedantic -g
BIN     := bin

.PHONY: all run run1 run2 run3 run4 symbols \
        ex1 ex2 ex3 sol1 sol2 sol3 clean

all: $(BIN)/hello \
     $(BIN)/02_use_static $(BIN)/03_use_dynamic $(BIN)/04_linkage \
     $(BIN)/ex_ex1_celsius $(BIN)/ex_ex3_symbols \
     $(BIN)/sol_ex1_celsius $(BIN)/sol_ex2_undefined $(BIN)/sol_ex3_symbols

$(BIN):
	mkdir -p $(BIN)

# ---------------------------------------------------------------------------
# Demo 1: the four stages, made visible. Each rule keeps the intermediate file.
#   -E preprocess  ->  .i   (macros expanded, #includes pasted in)
#   -S compile     ->  .s   (assembly)
#   -c assemble    ->  .o   (Mach-O object: machine code + symbol table)
#   link           ->  exe  (dyld-loadable executable)
# ---------------------------------------------------------------------------
$(BIN)/hello.i: hello.c | $(BIN)
	$(CC) $(CFLAGS) -E hello.c -o $@
$(BIN)/hello.s: hello.c | $(BIN)
	$(CC) $(CFLAGS) -S hello.c -o $@
$(BIN)/hello.o: hello.c | $(BIN)
	$(CC) $(CFLAGS) -c hello.c -o $@
$(BIN)/hello: $(BIN)/hello.o
	$(CC) $(CFLAGS) $(BIN)/hello.o -o $@

# ---------------------------------------------------------------------------
# Demo 2: STATIC library. Compile mymath.c -> .o, archive with `ar rcs`, then
# link the archive into the executable (symbols are COPIED in).
# ---------------------------------------------------------------------------
$(BIN)/mymath.o: mymath.c mymath.h | $(BIN)
	$(CC) $(CFLAGS) -c mymath.c -o $@
$(BIN)/libmymath.a: $(BIN)/mymath.o
	ar rcs $@ $<
$(BIN)/02_use_static: 02_use_static.c $(BIN)/libmymath.a
	$(CC) $(CFLAGS) 02_use_static.c -L$(BIN) -lmymath -o $@

# ---------------------------------------------------------------------------
# Demo 3: DYNAMIC library. Build a .dylib whose install name is @rpath-relative,
# then link the program with an rpath of @loader_path so dyld finds the library
# next to the executable (both land in bin/) at run time -- no DYLD_* env vars.
#   Linux/ELF: clang -shared -fPIC -o libmymath.so ...  then -Wl,-rpath,'$ORIGIN'
# ---------------------------------------------------------------------------
$(BIN)/libmymath.dylib: mymath.c mymath.h | $(BIN)
	$(CC) $(CFLAGS) -dynamiclib -install_name @rpath/libmymath.dylib \
	      mymath.c -o $@
$(BIN)/03_use_dynamic: 03_use_dynamic.c $(BIN)/libmymath.dylib
	$(CC) $(CFLAGS) 03_use_dynamic.c -L$(BIN) -lmymath \
	      -Wl,-rpath,@loader_path -o $@

# ---------------------------------------------------------------------------
# Demo 4: internal vs external linkage across two translation units.
# ---------------------------------------------------------------------------
$(BIN)/04_linkage.o: 04_linkage.c | $(BIN)
	$(CC) $(CFLAGS) -c 04_linkage.c -o $@
$(BIN)/04_helper.o: 04_helper.c | $(BIN)
	$(CC) $(CFLAGS) -c 04_helper.c -o $@
$(BIN)/04_linkage: $(BIN)/04_linkage.o $(BIN)/04_helper.o
	$(CC) $(CFLAGS) $(BIN)/04_linkage.o $(BIN)/04_helper.o -o $@

run: run1 run2 run3 run4

run1: $(BIN)/hello.i $(BIN)/hello.s $(BIN)/hello.o $(BIN)/hello
	@echo "── demo 1: the four build stages on hello.c ──"
	@echo "[1] preprocessed (bin/hello.i): macro + #include expanded — last lines:"
	@tail -n 6 $(BIN)/hello.i | sed 's/^/    /'
	@echo "[2] assembly (bin/hello.s): the call to puts — grep:"
	@grep -m1 -i 'puts' $(BIN)/hello.s | sed 's/^/    /'
	@echo "[3] object (bin/hello.o): Mach-O, symbol table —"
	@file $(BIN)/hello.o | sed 's/^/    /'
	@echo "[4] linked executable runs:"
	@./$(BIN)/hello | sed 's/^/    /'

run2: $(BIN)/02_use_static
	@echo "── demo 2: static library (libmymath.a) ──"
	@./$<

run3: $(BIN)/03_use_dynamic
	@echo "── demo 3: dynamic library (libmymath.dylib via dyld) ──"
	@./$<

run4: $(BIN)/04_linkage
	@echo "── demo 4: internal vs external linkage ──"
	@./$<

# Helper: inspect symbols/dependencies of the built binaries (Mach-O / dyld).
symbols: $(BIN)/02_use_static $(BIN)/03_use_dynamic $(BIN)/libmymath.a
	@echo "── nm libmymath.a (static archive members & their symbols) ──"
	@nm $(BIN)/libmymath.a
	@echo
	@echo "── nm bin/02_use_static  (static: mm_gcd is T = DEFINED in the binary) ──"
	@nm $(BIN)/02_use_static | grep -E 'mm_gcd|mm_ipow|_main'
	@echo
	@echo "── nm bin/03_use_dynamic (dynamic: mm_gcd is U = imported) ──"
	@nm $(BIN)/03_use_dynamic | grep -E 'mm_gcd|mm_ipow|_main'
	@echo
	@echo "── otool -L bin/03_use_dynamic (run-time shared-library deps) ──"
	@otool -L $(BIN)/03_use_dynamic

# --------------------------- exercises -------------------------------------
# ex1: split single-file program into libtemp.a + main that links it.
$(BIN)/ex1_celsius_lib.o: exercises/ex1_celsius_lib.c exercises/ex1_celsius.h | $(BIN)
	$(CC) $(CFLAGS) -c exercises/ex1_celsius_lib.c -o $@
$(BIN)/libtemp.a: $(BIN)/ex1_celsius_lib.o
	ar rcs $@ $<
$(BIN)/ex_ex1_celsius: exercises/ex1_celsius.c $(BIN)/libtemp.a
	$(CC) $(CFLAGS) exercises/ex1_celsius.c -L$(BIN) -ltemp -o $@
ex1: $(BIN)/ex_ex1_celsius ; ./$<

# ex2: EXPECTED to fail linking until you define the symbol. We don't stop the
# build of `all` on it — it is only built when you ask for `make ex2`.
ex2:
	@echo "── ex2: this link is SUPPOSED to fail (undefined symbol) ──"
	$(CC) $(CFLAGS) exercises/ex2_undefined.c -o $(BIN)/ex_ex2_undefined

# ex3: build, then dump its symbols / deps to inspect.
$(BIN)/ex_ex3_symbols: exercises/ex3_symbols.c | $(BIN)
	$(CC) $(CFLAGS) exercises/ex3_symbols.c -o $@
ex3: $(BIN)/ex_ex3_symbols
	@./$<
	@echo "── nm (T = defined here, U = imported) ──"
	@nm $< | grep -E 'my_square|_printf|_main'
	@echo "── otool -L (shared libraries) ──"
	@otool -L $<

# --------------------------- solutions -------------------------------------
$(BIN)/sol_ex1_celsius_lib.o: solutions/ex1_celsius_lib.c solutions/ex1_celsius.h | $(BIN)
	$(CC) $(CFLAGS) -c solutions/ex1_celsius_lib.c -o $@
$(BIN)/libtempsol.a: $(BIN)/sol_ex1_celsius_lib.o
	ar rcs $@ $<
$(BIN)/sol_ex1_celsius: solutions/ex1_celsius.c $(BIN)/libtempsol.a
	$(CC) $(CFLAGS) solutions/ex1_celsius.c -L$(BIN) -ltempsol -o $@
sol1: $(BIN)/sol_ex1_celsius ; ./$<

$(BIN)/sol_ex2_undefined: solutions/ex2_undefined.c | $(BIN)
	$(CC) $(CFLAGS) solutions/ex2_undefined.c -o $@
sol2: $(BIN)/sol_ex2_undefined ; ./$<

$(BIN)/sol_ex3_symbols: solutions/ex3_symbols.c | $(BIN)
	$(CC) $(CFLAGS) solutions/ex3_symbols.c -o $@
sol3: $(BIN)/sol_ex3_symbols
	@./$<
	@echo "── nm ──"
	@nm $< | grep -E 'my_square|_printf|_main'
	@echo "── otool -L ──"
	@otool -L $<

clean:
	rm -rf $(BIN)
