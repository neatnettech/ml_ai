# SOLUTION 45.2 — Let C write directly into a NumPy array (zero copy)

import ctypes
import os

import numpy as np

W, H, MAX_ITER = 200, 150, 100


def load_lib():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ("libmandel.dylib", "libmandel.so"):
        p = os.path.join(here, name)
        if os.path.exists(p):
            return ctypes.CDLL(p)
    raise FileNotFoundError("run `make lib` first")


def main():
    lib = load_lib()
    lib.mandelbrot.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                               ctypes.POINTER(ctypes.c_int)]
    lib.mandelbrot.restype = None

    # Contiguous int32 buffer owned by NumPy. mandel.c writes 32-bit ints (C `int`),
    # so the dtype MUST be int32 to match — a classic boundary gotcha.
    arr = np.zeros((H, W), dtype=np.int32)
    ptr = arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
    lib.mandelbrot(W, H, MAX_ITER, ptr)  # C fills arr's memory in place — no copy

    print(f"array sum={int(arr.sum())}, shape={arr.shape}")
    print("C wrote straight into NumPy-owned memory. That's how the ML stack avoids copies.")


if __name__ == "__main__":
    main()
