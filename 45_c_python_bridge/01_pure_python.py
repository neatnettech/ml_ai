# %% [markdown]
# Demo 1 — The kernel, in pure Python (the slow baseline)
#
# We compute a **Mandelbrot set** escape-count grid: for each complex point c, iterate
# z = z*z + c and count how many steps until |z| > 2 (or give up at max_iter). It's a
# tight numeric double-loop — exactly the kind of code Python is *slowest* at, because
# every `+` and `*` goes through the interpreter and boxes a new Python float object.
#
# Run: `python 01_pure_python.py`  (or `make run1`). This is the number every C/C++
# bridge in this module races against.

import time


def mandelbrot_pure(width, height, max_iter=100):
    """Return a flat list of escape counts (row-major), computed in pure Python."""
    out = [0] * (width * height)
    # Map pixels to the complex plane region [-2.5, 1.0] x [-1.25, 1.25]
    for py in range(height):
        y0 = -1.25 + 2.5 * py / height
        for px in range(width):
            x0 = -2.5 + 3.5 * px / width
            x = 0.0
            y = 0.0
            it = 0
            # iterate z = z^2 + c, with z = x + iy, c = x0 + iy0
            while x * x + y * y <= 4.0 and it < max_iter:
                x_new = x * x - y * y + x0
                y = 2.0 * x * y + y0
                x = x_new
                it += 1
            out[py * width + px] = it
    return out


def checksum(counts):
    """A cheap way to confirm every implementation computes the SAME grid."""
    return sum(counts)


if __name__ == "__main__":
    W, H, MAX_ITER = 600, 400, 100
    t0 = time.perf_counter()
    counts = mandelbrot_pure(W, H, MAX_ITER)
    dt = time.perf_counter() - t0
    print(f"pure Python : {dt*1000:8.1f} ms   checksum={checksum(counts)}")
    print(f"             ({W}x{H}, max_iter={MAX_ITER})")
    print("Remember this number — every C/C++ bridge below should crush it.")
