# Exercise 45.1 — Declare a C signature for ctypes
#
# ctypes can't introspect a .dylib; YOU must declare each function's argument and
# return types or calls will misbehave (wrong sizes, garbage, crashes). Fill in the
# `argtypes`/`restype` for `mandelbrot` and allocate the output buffer, then call it.
#
# Run `make ex1` (wrong/incomplete) then `make sol1`. The C signature is:
#     void mandelbrot(int width, int height, int max_iter, int *out);

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

    # TODO 1: declare the signature.
    #   lib.mandelbrot.argtypes = [ ... four entries ... ]
    #   lib.mandelbrot.restype  = None
    # Hint: ints are ctypes.c_int; the last arg is ctypes.POINTER(ctypes.c_int).

    # TODO 2: allocate an output buffer of W*H c_int and call lib.mandelbrot(...).
    buf = None  # replace with (ctypes.c_int * (W * H))()

    if buf is None:
        print("ex1 not implemented — fill in the TODOs (see solutions/).")
        return
    print(f"checksum={sum(buf)}  (compare with `make sol1`)")


if __name__ == "__main__":
    main()
