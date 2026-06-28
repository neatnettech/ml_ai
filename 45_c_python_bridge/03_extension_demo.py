# %% [markdown]
# Bridge 2 — import a C extension like any Python module
#
# After `make ext` (which runs `python setup.py build_ext --inplace`), there is a
# compiled `mandelext.*.so` in this directory and you can simply `import mandelext`.
# From Python's side it's indistinguishable from a pure-Python module — but the work
# runs in C. This is exactly how CPython's own built-in modules are shipped.
#
# Run: `make run3`.

import time
from importlib import import_module

pure = import_module("01_pure_python")

try:
    import mandelext
    HAVE_EXT = True
except ImportError:
    HAVE_EXT = False


if __name__ == "__main__":
    if not HAVE_EXT:
        print("[skipped] mandelext not built — run `make ext` first "
              "(needs Python dev headers; they ship with python.org / Homebrew Python).")
        raise SystemExit(0)

    W, H, MAX_ITER = 600, 400, 100
    t0 = time.perf_counter()
    counts = mandelext.compute(W, H, MAX_ITER)
    dt = time.perf_counter() - t0

    print(f"C extension  : {dt*1000:8.1f} ms   checksum={sum(counts)}")
    ref = pure.mandelbrot_pure(W, H, MAX_ITER)
    print(f"matches pure Python? {sum(counts) == pure.checksum(ref)}")
    print(f"help(mandelext.compute): {mandelext.compute.__doc__}")
    print("You just called C with `import`. That's what NumPy/PyTorch do underneath.")
