# %% [markdown]
# Bridge 3 — call a C++ function bound with pybind11
#
# After `make pybind` (also `setup.py build_ext --inplace`), `import mandelpy` loads the
# C++ extension. The C++ source was ~25 lines with no manual ref-counting — pybind11
# generated the glue. Same speed class as the hand-written C extension, far less
# boilerplate. This is how modern native packages bind C++ to Python (ties to Module 44).
#
# Run: `make run4`.

import time
from importlib import import_module

pure = import_module("01_pure_python")

try:
    import mandelpy
    HAVE_PYBIND = True
except ImportError:
    HAVE_PYBIND = False


if __name__ == "__main__":
    if not HAVE_PYBIND:
        print("[skipped] mandelpy not built — run `pip install pybind11` then `make pybind`.")
        raise SystemExit(0)

    W, H, MAX_ITER = 600, 400, 100
    t0 = time.perf_counter()
    counts = mandelpy.compute(width=W, height=H, max_iter=MAX_ITER)  # keyword args!
    dt = time.perf_counter() - t0

    print(f"C++ pybind11 : {dt*1000:8.1f} ms   checksum={sum(counts)}")
    ref = pure.mandelbrot_pure(W, H, MAX_ITER)
    print(f"matches pure Python? {sum(counts) == pure.checksum(ref)}")
    print("pybind11 even gave us keyword arguments + a docstring for free.")
