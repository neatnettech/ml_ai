# SOLUTION 45.3 — Vectorize a slow loop with NumPy

import time

import numpy as np


def slow(n):
    total = 0
    for i in range(n):
        total += i * i
    return total


def fast(n):
    # int64 to avoid overflow on the squares + their sum.
    i = np.arange(n, dtype=np.int64)
    return int((i * i).sum())


def main():
    n = 2_000_000
    t0 = time.perf_counter(); s = slow(n); t_slow = time.perf_counter() - t0
    t0 = time.perf_counter(); f = fast(n); t_fast = time.perf_counter() - t0
    print(f"slow {t_slow*1000:7.1f} ms | fast {t_fast*1000:7.1f} ms | "
          f"speedup {t_slow/t_fast:.1f}x | match={s == int(f)}")
    print("Same answer; the loop now runs in NumPy's C core instead of the interpreter.")


if __name__ == "__main__":
    main()
