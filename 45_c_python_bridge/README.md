# Module 45 — C/C++ ↔ Python (FFI & Extensions)

**Purpose:** This is the **bridge between Track 6 (the C/C++ bytes-up track) and the
Python tracks (1–2 ML, 3 backend)** — and the answer to "is Python based on C?" **Yes:**
the reference interpreter, **CPython**, is written in C; `list`/`dict`/`int` are C
structs, and NumPy/pandas/PyTorch are C/C++ cores under a thin Python skin. Here you
take **one compute kernel (the Mandelbrot set)** and call it from Python **four ways** —
ctypes, a CPython C-API extension, a pybind11/C++ extension, and NumPy — then benchmark
them against pure Python so you *see* why the whole ML stack is C underneath.

**Prerequisites:** Module 30 (C pointers/memory), Module 34 (dynamic libraries — ctypes
loads exactly such a `.dylib`), Module 44 (C++, for the pybind11 bridge); Module 1
(NumPy) for the vectorized comparison.

**What you'll learn:**
- Why pure-Python numeric loops are slow (the interpreter boxes every value) and how to fix it
- **ctypes** — call a compiled C `.dylib` with zero Python build step
- **CPython C-API** — write a real `.c` extension you `import` (the literal "Python is C")
- **pybind11** — bind modern C++ to Python with almost no boilerplate (how PyTorch et al. do it)
- **NumPy** — push the loop into a C core without writing C yourself
- Sharing buffers across the boundary **zero-copy**, and the GIL/marshalling costs

> **Format:** this module mixes C, C++, and Python. Use the **same Python that has
> `numpy` + `pybind11`** (your project venv). The Makefile takes `PYTHON=...`:
> ```bash
> make all PYTHON=../.venv/bin/python    # build the .dylib + both extensions
> make run PYTHON=../.venv/bin/python    # build everything, run the benchmark
> ```
> `pip install pybind11` if it's missing (the C++ bridge is skipped gracefully without it).

## The kernel

Mandelbrot escape counts: for each pixel's complex point `c`, iterate `z = z² + c` and
count steps until `|z| > 2` (cap at `max_iter`). A tight numeric double-loop — exactly
where Python is slowest and C shines. Every implementation computes the **identical
grid**, confirmed by a shared checksum.

## The four bridges

### Bridge 1 — ctypes ([`mandel.c`](mandel.c) → [`02_ctypes_demo.py`](02_ctypes_demo.py))
`mandel.c` is an ordinary C function compiled to `libmandel.dylib` (the Module 34 idea).
`ctypes` (stdlib) loads it at runtime; you declare the signature and call it. No Python
build step. **Gotcha:** loading a freshly built `.dylib` pays a one-time `dlopen` /
code-sign cost — load it **once**, not per call.

### Bridge 2 — CPython C-API ([`mandelext.c`](mandelext.c) → [`03_extension_demo.py`](03_extension_demo.py))
A real extension module written against `<Python.h>`: it parses args from Python objects
(`PyArg_ParseTuple`) and builds a Python list to return (`PyList_New`/`PyLong_FromLong`).
After `make ext` you just `import mandelext`. **This is literally how CPython's own
built-in modules ship.**

### Bridge 3 — pybind11 / C++ ([`mandel_pybind.cpp`](mandel_pybind.cpp) → [`04_pybind_demo.py`](04_pybind_demo.py))
The same kernel in idiomatic C++; one `PYBIND11_MODULE` block generates all the glue —
no manual ref-counting, and you get keyword args + a docstring for free. Compare its ~25
lines to `mandelext.c`'s ~60. Ties to Module 44.

### Bridge 4 — NumPy ([`05_numpy_demo.py`](05_numpy_demo.py))
Not a different language — NumPy *is* a C library with a Python skin. Express the grid as
array ops and the loop runs in NumPy's compiled core. Shows "Python is slow" really means
"the *interpreter loop* is slow."

Both compiled extensions are built by [`setup.py`](setup.py) (`build_ext --inplace`).

## Benchmark (`make run`)

Real output on this Apple Silicon machine (your numbers will vary; the **ratios** are the
lesson). All five compute the same grid — note `correct? yes` on every row:

```
Mandelbrot 600x400, max_iter=100
method             time (ms)   speedup   correct?
----------------------------------------------------
pure Python            371.3      1.0x   yes
C (ctypes)              12.9     28.7x   yes
C extension             11.7     31.7x   yes
C++ (pybind11)          16.6     22.3x   yes
NumPy vector            74.3      5.0x   yes
```

Takeaways: the three native bridges all land ~20–30× over pure Python and within a
hair of each other (same C math; the boundary cost is per-*call*, not per-*iteration*).
NumPy's ~5× is "free" (no compiler) but its vectorized form still allocates whole-array
temporaries. The benchmark also writes `mandelbrot.png` so you can see the kernel is real.

## Exercises

Stubs in `exercises/` (`// TODO`), reference answers in `solutions/`. `make exN` / `make solN`.

- **45.1 — Declare a C signature for ctypes** ([ex1](exercises/ex1_ctypes_declare.py)):
  fill in `argtypes`/`restype` and call the C function. Why the declaration matters.
- **45.2 — Zero-copy NumPy ↔ C** ([ex2](exercises/ex2_numpy_zerocopy.py)): hand C the raw
  pointer to a NumPy array so it writes **in place** — the pattern behind the ML stack's
  no-copy buffers (watch the `int32` dtype match!).
- **45.3 — Vectorize without C** ([ex3](exercises/ex3_numpy_vectorize.py)): turn a slow
  pure-Python loop into NumPy array ops; verify same result + measure the speedup.

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **CPython is C** | The interpreter and built-in types are C; "Python is slow" = the interpreter loop is slow |
| **ctypes** | Call any compiled `.dylib`/`.so` from Python with no build step — reuses Module 34 |
| **C-API extension** | Write/`import` a real C module; how built-ins and many packages ship |
| **pybind11** | Bind C++ to Python with minimal boilerplate — the modern native-package path (Module 44) |
| **NumPy** | Vectorization pushes the loop into a C core without writing C |
| **Zero-copy buffers** | Sharing a pointer (not copying) across the boundary is how NumPy/PyTorch stay fast |
| **Where the boundary cost lives** | dlopen/marshalling/GIL are per-call; keep the hot loop *inside* C |

## Further reading

- **Python C-API — Extending and Embedding** (official): https://docs.python.org/3/extending/index.html
- **ctypes** (official): https://docs.python.org/3/library/ctypes.html
- **pybind11 docs**: https://pybind11.readthedocs.io/  ·  **nanobind** (its faster successor): https://nanobind.readthedocs.io/
- **NumPy internals / C-API**: https://numpy.org/doc/stable/reference/c-api/
- **CPython source** (read `Objects/listobject.c` to see a built-in type *is* a C struct):
  https://github.com/python/cpython

**Next:** You've connected both halves of the catalog — the Python ML tracks now rest on
the C/C++ foundations you built in Track 6. See [the track plan](../cs-foundations-track.md)
for the full map.
