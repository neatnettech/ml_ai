# SOLUTION 45.1 — Declare a C signature for ctypes

import ctypes
import os

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

    buf = (ctypes.c_int * (W * H))()
    lib.mandelbrot(W, H, MAX_ITER, buf)
    print(f"checksum={sum(buf)}")
    print("Declaring argtypes/restype is what makes the C call safe and correct.")


if __name__ == "__main__":
    main()
