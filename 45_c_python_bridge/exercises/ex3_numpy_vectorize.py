# Exercise 45.3 — Make Python fast WITHOUT C, by pushing the loop into NumPy
#
# Not every speedup needs a compiler. A slow pure-Python numeric loop often becomes
# fast just by expressing it as NumPy array ops (the loop then runs in NumPy's C core).
# Below is a slow function; implement `fast` to return the identical result with NO
# Python-level loop, and the harness checks it matches AND times both.
#
# Run `make ex3` then `make sol3`.

import time

import numpy as np


def slow(n):
    """Sum of i*i for i in [0, n), the slow interpreter-loop way."""
    total = 0
    for i in range(n):
        total += i * i
    return total


def fast(n):
    # TODO: return the same value with no Python loop.
    # Hint: np.arange(n, dtype=np.int64); square; sum. Watch the dtype (avoid overflow).
    return None


def main():
    n = 2_000_000
    t0 = time.perf_counter(); s = slow(n); t_slow = time.perf_counter() - t0
    t0 = time.perf_counter(); f = fast(n); t_fast = time.perf_counter() - t0
    if f is None:
        print("ex3 not implemented — fill in `fast` (see solutions/).")
        return
    print(f"slow {t_slow*1000:7.1f} ms | fast {t_fast*1000:7.1f} ms | "
          f"speedup {t_slow/t_fast:.1f}x | match={s == int(f)}")


if __name__ == "__main__":
    main()
