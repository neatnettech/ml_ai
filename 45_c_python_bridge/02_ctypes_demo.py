# %% [markdown]
# Bridge 1 — ctypes: call a C shared library from Python, no build step in Python
#
# `ctypes` is in the Python standard library. It loads a compiled `.dylib`/`.so` at
# runtime and lets you call its C functions directly — you just declare the argument
# and return types. No C compiler is invoked by Python here; we built `libmandel.dylib`
# with the Makefile (`make lib`). This is the lowest-friction C<->Python bridge and it
# reuses the exact dynamic-library idea from Module 34.
#
# Run: `make run2` (the Makefile builds libmandel.dylib first).

import ctypes
import os
import time

from importlib import import_module

pure = import_module("01_pure_python")  # reuse the baseline + checksum


_LIB = None  # cache: loading (dlopen) a freshly built .dylib costs ~hundreds of ms
             # the first time (macOS code-signing check), so load it ONCE, not per call.


def load_lib():
    """Load libmandel.dylib (macOS) or libmandel.so (Linux), memoized."""
    global _LIB
    if _LIB is not None:
        return _LIB
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("libmandel.dylib", "libmandel.so"):
        path = os.path.join(here, name)
        if os.path.exists(path):
            _LIB = ctypes.CDLL(path)
            _LIB.mandelbrot.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                        ctypes.POINTER(ctypes.c_int)]
            _LIB.mandelbrot.restype = None
            return _LIB
    raise FileNotFoundError("Build the library first: run `make lib`")


def mandelbrot_ctypes(width, height, max_iter=100):
    lib = load_lib()  # signature already declared in load_lib()
    # Allocate a C array Python owns, hand its pointer to C to fill in.
    buf = (ctypes.c_int * (width * height))()
    lib.mandelbrot(width, height, max_iter, buf)
    return buf  # a ctypes array; indexable like a list


if __name__ == "__main__":
    W, H, MAX_ITER = 600, 400, 100

    t0 = time.perf_counter()
    buf = mandelbrot_ctypes(W, H, MAX_ITER)
    dt = time.perf_counter() - t0

    cs = sum(buf)  # checksum over the ctypes array
    print(f"C via ctypes : {dt*1000:8.1f} ms   checksum={cs}")

    # Confirm it matches the pure-Python grid exactly (correctness before speed).
    ref = pure.mandelbrot_pure(W, H, MAX_ITER)
    print(f"matches pure Python? {cs == pure.checksum(ref)}")
    print("Same answer, a fraction of the time — and ctypes needed no Python build step.")
