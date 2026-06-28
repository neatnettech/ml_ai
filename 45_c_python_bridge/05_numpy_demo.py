# %% [markdown]
# The fourth way — NumPy: vectorized Python that's ALSO C underneath
#
# NumPy isn't a different language — it's a C library with a Python skin (Track 1,
# Module 1). Instead of looping in Python, you express the whole grid as array
# operations; the loops run in NumPy's compiled C core. This shows that the "Python is
# slow" story is really "the Python *interpreter loop* is slow" — push the loop into C
# (your own, or NumPy's) and it flies.
#
# Run: `make run5`.

import time
from importlib import import_module

import numpy as np

pure = import_module("01_pure_python")


def mandelbrot_numpy(width, height, max_iter=100):
    """Vectorized Mandelbrot: no Python-level per-pixel loop, only per-iteration."""
    xs = np.linspace(-2.5, 1.0, width, endpoint=False, dtype=np.float64)
    ys = np.linspace(-1.25, 1.25, height, endpoint=False, dtype=np.float64)
    c = xs[np.newaxis, :] + 1j * ys[:, np.newaxis]   # (height, width) complex grid
    z = np.zeros_like(c)
    counts = np.zeros(c.shape, dtype=np.int32)
    alive = np.ones(c.shape, dtype=bool)
    # Match the pure-Python counting order exactly: update z, count the step for every
    # still-alive point, THEN drop the ones that just escaped. (Off-by-one lives here —
    # counting before vs after the escape test gives different grids.)
    for _ in range(max_iter):
        z[alive] = z[alive] * z[alive] + c[alive]
        counts[alive] += 1
        escaped = alive & (z.real * z.real + z.imag * z.imag > 4.0)
        alive &= ~escaped
    return counts


if __name__ == "__main__":
    W, H, MAX_ITER = 600, 400, 100
    t0 = time.perf_counter()
    counts = mandelbrot_numpy(W, H, MAX_ITER)
    dt = time.perf_counter() - t0
    cs = int(counts.sum())
    print(f"NumPy vector : {dt*1000:8.1f} ms   checksum={cs}")
    ref_cs = pure.checksum(pure.mandelbrot_pure(W, H, MAX_ITER))
    print(f"matches pure Python? {cs == ref_cs}  (ref={ref_cs})")
    print("Same C-under-the-hood lesson — NumPy just ships the C loop for you.")
