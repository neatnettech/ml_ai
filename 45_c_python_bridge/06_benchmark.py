# %% [markdown]
# The payoff — benchmark all five implementations side by side
#
# Runs whichever bridges are built, times each on the same grid, confirms they all
# compute the IDENTICAL result (checksum), and prints a speedup table vs pure Python.
# Optionally saves the Mandelbrot image (matplotlib) so you see the kernel is real.
#
# Run: `make run` (builds the lib + extensions first) or `python 06_benchmark.py`.

import time
from importlib import import_module

pure = import_module("01_pure_python")
ctypes_demo = import_module("02_ctypes_demo")
numpy_demo = import_module("05_numpy_demo")


def timed(fn, *args):
    # Warm up once (discarded): the first call to a native bridge can include one-time
    # costs — dlopen/code-sign of a fresh .dylib, lazy symbol binding — that aren't the
    # compute we want to measure. Time the second call.
    fn(*args)
    t0 = time.perf_counter()
    out = fn(*args)
    return (time.perf_counter() - t0), out


def main(W=600, H=400, MAX_ITER=100, save_image=True):
    results = []  # (name, ms, checksum)

    # 1) pure Python (the baseline)
    dt, counts = timed(pure.mandelbrot_pure, W, H, MAX_ITER)
    ref_cs = pure.checksum(counts)
    results.append(("pure Python", dt, ref_cs))
    grid_for_image = counts

    # 2) C via ctypes (build with `make lib`)
    try:
        dt, buf = timed(ctypes_demo.mandelbrot_ctypes, W, H, MAX_ITER)
        results.append(("C (ctypes)", dt, sum(buf)))
    except FileNotFoundError:
        results.append(("C (ctypes)", None, None))

    # 3) CPython C-API extension (build with `make ext`)
    try:
        mandelext = import_module("mandelext")
        dt, counts = timed(mandelext.compute, W, H, MAX_ITER)
        results.append(("C extension", dt, sum(counts)))
    except ImportError:
        results.append(("C extension", None, None))

    # 4) C++ via pybind11 (build with `make pybind`)
    try:
        mandelpy = import_module("mandelpy")
        dt, counts = timed(mandelpy.compute, W, H, MAX_ITER)
        results.append(("C++ (pybind11)", dt, sum(counts)))
    except ImportError:
        results.append(("C++ (pybind11)", None, None))

    # 5) NumPy vectorized
    dt, counts = timed(numpy_demo.mandelbrot_numpy, W, H, MAX_ITER)
    results.append(("NumPy vector", dt, int(counts.sum())))

    # Report
    base = results[0][1]
    print(f"Mandelbrot {W}x{H}, max_iter={MAX_ITER}\n")
    print(f"{'method':<16}{'time (ms)':>12}{'speedup':>10}   correct?")
    print("-" * 52)
    for name, dt, cs in results:
        if dt is None:
            print(f"{name:<16}{'(not built)':>12}{'':>10}")
            continue
        speed = base / dt
        ok = "yes" if cs == ref_cs else f"NO ({cs})"
        print(f"{name:<16}{dt*1000:>12.1f}{speed:>9.1f}x   {ok}")

    if save_image:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import numpy as np
            img = np.array(grid_for_image, dtype=np.int32).reshape(H, W)
            plt.figure(figsize=(7, 5))
            plt.imshow(img, cmap="twilight_shifted", extent=(-2.5, 1.0, -1.25, 1.25))
            plt.title("Mandelbrot escape counts")
            plt.tight_layout()
            plt.savefig("mandelbrot.png", dpi=110)
            print("\nSaved mandelbrot.png")
        except Exception as e:
            print(f"\n(image skipped: {e})")


if __name__ == "__main__":
    main()
