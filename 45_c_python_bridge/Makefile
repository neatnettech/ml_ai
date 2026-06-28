# Module 45 — C/C++ <-> Python (FFI & Extensions)
#
# Unlike the rest of Track 6, this module mixes C, C++, and Python. Use the SAME Python
# that has numpy/pybind11 (your project venv). Pass it explicitly if `python3` isn't it:
#   make all   PYTHON=../.venv/bin/python
#   make run   PYTHON=../.venv/bin/python
#
# Targets:
#   make all       build the ctypes lib + both compiled extensions
#   make lib       build libmandel.<dylib|so> for the ctypes bridge
#   make ext       build the C and C++ extensions (setup.py build_ext --inplace)
#   make run       build everything, then run the benchmark (06)
#   make run1..5   run a single demo
#   make ex1..3 / sol1..3   exercises / solutions
#   make clean     remove all build artifacts

PYTHON ?= python3
CC     ?= clang

UNAME := $(shell uname)
ifeq ($(UNAME),Darwin)
LIBEXT := dylib
else
LIBEXT := so
endif

.PHONY: all lib ext pybind run run1 run2 run3 run4 run5 \
        ex1 ex2 ex3 sol1 sol2 sol3 clean

all: lib ext

# --- Bridge 1: ctypes needs only a plain shared library (no Python build) ---
lib: libmandel.$(LIBEXT)

libmandel.$(LIBEXT): mandel.c
	$(CC) -O3 -shared -fPIC $< -o $@

# --- Bridges 2 & 3: compiled Python extensions via setuptools ---
# setup.py builds mandelext (C-API) always, and mandelpy (pybind11/C++) if pybind11 is
# installed. `ext` and `pybind` are the same build step.
ext:
	$(PYTHON) setup.py build_ext --inplace

pybind: ext

# --- Run demos / benchmark ---
run: all ext
	$(PYTHON) 06_benchmark.py

run1: ; $(PYTHON) 01_pure_python.py
run2: lib ; $(PYTHON) 02_ctypes_demo.py
run3: ext ; $(PYTHON) 03_extension_demo.py
run4: ext ; $(PYTHON) 04_pybind_demo.py
run5: ; $(PYTHON) 05_numpy_demo.py

ex1: lib ; $(PYTHON) exercises/ex1_ctypes_declare.py
ex2: lib ; $(PYTHON) exercises/ex2_numpy_zerocopy.py
ex3: ; $(PYTHON) exercises/ex3_numpy_vectorize.py

sol1: lib ; $(PYTHON) solutions/ex1_ctypes_declare.py
sol2: lib ; $(PYTHON) solutions/ex2_numpy_zerocopy.py
sol3: ; $(PYTHON) solutions/ex3_numpy_vectorize.py

clean:
	rm -rf build *.so *.dylib *.o __pycache__ mandelbrot.png \
	       exercises/__pycache__ solutions/__pycache__
