# Exercise 45.2 — Let C write directly into a NumPy array (zero copy)
#
# The real-world pattern behind NumPy/PyTorch C backends: Python allocates the array,
# C fills it IN PLACE — no copying across the boundary. Allocate an int32 NumPy array,
# pass its raw data pointer to the C `mandelbrot`, and check C actually wrote into it.
#
# Run `make ex2` then `make sol2`. Same C signature as ex1.

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

    # TODO 1: make a CONTIGUOUS int32 numpy array of shape (H, W), zero-filled.
    arr = None  # np.zeros((H, W), dtype=np.int32)

    # TODO 2: get a C int* to its buffer and call C to fill it IN PLACE.
    # Hint: ptr = arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
    #       lib.mandelbrot(W, H, MAX_ITER, ptr)

    if arr is None:
        print("ex2 not implemented — fill in the TODOs (see solutions/).")
        return
    print(f"array sum={int(arr.sum())}, shape={arr.shape}  (compare with `make sol2`)")


if __name__ == "__main__":
    main()
