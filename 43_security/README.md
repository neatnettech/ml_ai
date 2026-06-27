# Module 43 — Security & Cryptography Foundations

**Purpose:** Most security bugs are not exotic — they are the predictable consequence
of how C lays bytes out in memory and how integers wrap (Module 28). This module is
the *foundations* layer under the applied work you already did: the
[White-Hat track](../21_networking_and_packets/) (Modules 21–26) attacks running
services, and [Module 18](../18_cryptography/) uses real crypto libraries. Here we go
one level down and *see why those vulnerabilities exist* — a fixed buffer overrun into
its neighbour, a format string that becomes a write primitive, a multiply that wraps
into a tiny allocation — and we build the crypto **primitives** (XOR, a hash, a
constant-time compare) so the theory under Module 18 stops being a black box. Every
"vulnerable" demo here is **explain-and-fix**: it runs safely, never hijacks control
flow, and is paired with the corrected code.

## ⚠️ Read this first — ethics & scope

This is **white-hat, defensive, educational** material. The goal is to *understand and
prevent* these bugs, not to weaponise them.

1. **Nothing here is an exploit.** There is no shellcode, no return-address hijack, no
   working attack payload. The "vulnerable" demos illustrate the *root cause* on data
   the program owns, then show the fix. They compile warning-clean and terminate
   normally.
2. **Only test systems you own or have *written* permission to test.** In the US the
   relevant law is the **Computer Fraud and Abuse Act (CFAA)**; most countries have an
   equivalent (UK Computer Misuse Act, etc.). This applies the moment you take these
   ideas off your own machine.
3. **Defence is the point.** For every bug we name the mitigation (bounds checks,
   `snprintf`, constant format strings, checked multiplication, constant-time compares,
   and the compiler/OS hardening below).
4. **Practice legally and for free** on TryHackMe, Hack The Box, PortSwigger Web
   Security Academy, OverTheWire, the bundled [vulnlab](../23_web_app_security/), and
   your own VMs.

**Prerequisites:** [Module 18](../18_cryptography/) (applied crypto),
[Module 28](../28_bits_and_bytes/) (bytes, two's complement, wraparound),
[Module 30](../30_c_programming_i/) (pointers, stack vs heap). Ties forward to the
White-Hat [Module 23 vulnlab](../23_web_app_security/) — the same bug classes, one
abstraction layer up.

**What you'll learn:**
- **Memory-safety bugs** at the byte level: stack buffer overflow into an adjacent
  field, format-string bugs, integer-overflow → undersized allocation
- **How a real stack smash reaches the saved return address** — and the layered
  mitigations that stop it: stack canaries, ASLR, NX/W^X, `-D_FORTIFY_SOURCE`
- **Crypto primitives by hand** (educational): XOR cipher + the key-reuse break,
  Caesar/ROT, an FNV-1a checksum-hash
- **Timing side-channels** and the **constant-time comparison** that defeats them
  (the foundation under Module 18's "use a real library" advice)

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 43 runs **natively on Apple Silicon** — no container needed. You only need
`clang` + `make` (Xcode Command Line Tools):

```bash
make            # build all demos + exercises + solutions (zero warnings)
make run        # build + run all four demos
```

The build is `clang -std=c11 -Wall -Wextra -Wpedantic -g`. The vulnerable demos are
deliberately written so they compile **warning-clean** *and* run **without crashing or
invoking undefined behaviour** — the corruption is confined to data the program owns
(see each section for exactly what is "real" vs "illustrated").

---

## 1. Stack buffer overflow (`make run1`)

A fixed-size buffer with an unbounded copy is the oldest memory-safety bug there is.
[`01_buffer_overflow.c`](01_buffer_overflow.c) puts an 8-byte `name` buffer right next
to an `int is_admin` in the same struct, then copies a too-long input into `name`. The
extra bytes spill into the **adjacent field** — observable, in-bounds of the struct, no
crash:

```
=== Buffer overflow: corrupting an ADJACENT field (safe demo) ===

before: name="guest"  is_admin=0
after : name="AAAAAAA"  is_admin=1   <- overflow flipped is_admin!
        a 7-char name should NOT grant admin — the copy ran past name[]

=== Same input through the bounds-checked version ===
after : name="AAAAAAA"  is_admin=0   <- truncated, is_admin untouched
```

**What's real vs illustrated:** the copy genuinely writes past `name[]` into
`is_admin` — that privilege-flip is real corruption of a sibling field. What we do
*not* do is keep writing until we reach the function's **saved return address**.

**How a *real* stack smash escalates:** a stack frame holds local buffers, saved
registers, and the **return address** the CPU jumps to when the function returns. An
unbounded copy that runs far enough overwrites that saved address; on `ret` the CPU
jumps wherever the attacker wrote — into injected code, or (defeating NX) into a chain
of existing code gadgets (ROP). That is a control-flow hijack, and we deliberately
**do not** demonstrate it.

**The fix** is to bound every copy by the *destination* capacity and always
NUL-terminate — `snprintf(dst, sizeof dst, "%s", src)` or an explicit length. Never let
the *input* decide how many bytes you write.

**Defence in depth (the mitigations that make hijacks hard):**

| Mitigation | What it does |
|------------|--------------|
| **Stack canary** (`-fstack-protector`) | a random guard value placed before the saved return address; checked on return — a lazy overflow trips it and the program aborts |
| **ASLR** | randomises stack/heap/library base addresses each run, so the attacker can't predict where to jump |
| **NX / W^X** | marks the stack non-executable, so injected bytes can't run as code |
| **`-D_FORTIFY_SOURCE=2`** | swaps `memcpy`/`strcpy`/`sprintf` for bounds-aware variants when the size is known at compile time |

These are layers, not a cure: the only real fix is **not writing out of bounds**.

## 2. Format-string bug (`make run2`)

`printf(user_input)` is a bug even when today's input is harmless, because the user's
string *is* the format string. [`02_format_string.c`](02_format_string.c) shows the
shape of the bug on benign data, then the fix:

```
vulnerable call, benign input : user 'alice' logged in
safe call,       benign input : user 'alice' logged in

Why the vulnerable form is dangerous (NOT executed here):
  - "%x %x %x" -> printf reads values never passed -> INFO LEAK
  - "%n"        -> printf WRITES the byte-count to a pointer -> MEMORY WRITE
```

If the input contained `%x %x %x`, `printf` would read arguments that were never
passed — walking the stack and **leaking memory**. Worse, `%n` *writes* the number of
bytes printed so far to a pointer argument, turning a log call into an **arbitrary
memory write**. We never feed the vulnerable path a malicious string, so no
out-of-bounds varargs access happens.

**The fix** is one line: pass a constant format and put user data in a `%s`
argument — `printf("%s\n", user_input)`. The compiler helps: `-Wformat-security`
flags `printf(non_literal)`. (The demo locally silences that one warning around the
intentionally-wrong line so the file builds clean — in real code, leave it on.)

## 3. Integer overflow → undersized allocation (`make run3`)

Computing an allocation size as `count * elem` can **wrap** past `SIZE_MAX` (Module
28: unsigned arithmetic is mod 2^N). The result is a buffer far smaller than intended;
writing `count*elem` real bytes into it is then a **heap overflow**.
[`03_integer_overflow.c`](03_integer_overflow.c) shows the wrap and the fixes — and
*detects* the undersized buffer instead of writing past it:

```
Vulnerable multiply (count=4611686018427387904, elem=8):
  requested: 4611686018427387904 * 8 = 0 bytes (wrapped if tiny!)
  -> allocation is UNDERSIZED; a real bug would now overflow the heap.
     (demo refuses to write — no corruption performed)

Fix #1 — explicit overflow check before *:
  refused: 4611686018427387904 * 8 would overflow size_t
  a legitimate request (count=16, elem=8):
    ok: allocated and zeroed 128 bytes

Fix #2 — calloc() does the overflow check for you:
  calloc returned NULL (overflow or OOM) — handled safely
```

**The fixes:** check `count > SIZE_MAX / elem` *before* multiplying and refuse on
overflow, or use `calloc(count, elem)` which performs that check internally and
returns `NULL` on overflow.

## 4. Crypto primitives — for learning only (`make run4`)

[`04_crypto_primitives.c`](04_crypto_primitives.c) implements small, clearly-labelled
**educational** primitives. They build intuition for Module 18's theory; they are
**not secure** and must never protect anything real.

```
(a) XOR cipher
    plaintext : 61747461636b206174206461776e
    ciphertext: fe5805fe4f1abf4d05bf4810e842
    decrypted : 61747461636b206174206461776e
    key reuse: c1^c2 == p1^p2 ? yes  (the key cancels -> info leak)

(b) Caesar shift (+3)
    "Hello, ROT-3!" -> "Khoor, URW-3!" -> "Hello, ROT-3!"

(c) FNV-1a hash (non-cryptographic)
    fnv1a("hello") = 0x4f9f2cab
    fnv1a("hellp") = 0x5c9f4122  (one byte changed)

(d) Tag comparison: naive vs constant-time
    naive(correct)        = 1   constant_time(correct)        = 1
    naive(wrong)          = 0   constant_time(wrong)          = 0
    naive returns early on the first mismatch -> its TIMING leaks how many
    leading bytes were right. Always compare secrets in constant time.
```

- **(a) XOR cipher** is symmetric (XOR is its own inverse). Its fatal weakness:
  encrypting two messages under the **same keystream** leaks their XOR, because
  `c1 ^ c2 == p1 ^ p2` (the key cancels). This is exactly the "two-time pad" break.
- **(b) Caesar/ROT** shifts letters by a fixed amount — trivially broken by frequency
  analysis, but a clean first cipher.
- **(c) FNV-1a** is a real, simple *non-cryptographic* hash (great for hash tables,
  no collision resistance against an adversary). For a secure digest use
  SHA-256/BLAKE2.
- **(d) Constant-time comparison** is the load-bearing idea. A naive `memcmp`-style
  loop returns on the first mismatch, so its **running time leaks how many leading
  bytes matched** — enough to recover a secret tag byte by byte (a *timing
  side-channel*). The constant-time version always touches every byte and branches
  once at the end. This is why Module 18 says "use a vetted library": getting compare,
  padding, and key handling timing-safe by hand is hard.

**For real use:** [libsodium](https://doc.libsodium.org/), or the cryptography library
from [Module 18](../18_cryptography/).

---

## 5. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`.

### Exercise 43.1 — Make a copy bounds-safe  (`make ex1`)
Rewrite the vulnerable `copy_name` in
[`exercises/ex1_copy_name.c`](exercises/ex1_copy_name.c) so it never writes past the
destination and always NUL-terminates. Expected (`make sol1`):
```
short input  -> "bob"
long input   -> "superca"  (must be <= 7 chars, NUL-terminated)
```

### Exercise 43.2 — Constant-time equality  (`make ex2`)
Implement `ct_equal` in
[`exercises/ex2_constant_time_eq.c`](exercises/ex2_constant_time_eq.c) so the running
time does not depend on where the buffers differ, and explain in a comment *why* that
defeats the timing attack. Expected (`make sol2`):
```
ct_equal(tag, same)  = 1  (expect 1)
ct_equal(tag, diff1) = 0  (expect 0)
ct_equal(tag, diff4) = 0  (expect 0)
```

### Exercise 43.3 — Checked allocation size  (`make ex3`)
Add the overflow guard to `alloc_size` in
[`exercises/ex3_checked_alloc_size.c`](exercises/ex3_checked_alloc_size.c) so it
refuses sizes that would wrap. The stub (which has the bug) reports the overflow case
as `0 bytes (ok)`; the fixed version refuses it. Expected (`make sol3`):
```
count=16 elem=8 -> 128 bytes (ok)
count=0 elem=8 -> 0 bytes (ok)
count=4611686018427387904 elem=8 -> REFUSED (overflow)
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **Stack buffer overflow** | an unbounded copy corrupts neighbours and, far enough, the saved return address → control-flow hijack; fix = bound by the destination |
| **Hardening layers** | canaries, ASLR, NX/W^X, `-D_FORTIFY_SOURCE` raise the bar — but only *not* overflowing actually fixes the bug |
| **Format-string bugs** | user data used *as* a format string enables `%x` info leaks and `%n` memory writes; fix = constant format + `%s` |
| **Integer overflow** | `n*size` wraps to a tiny allocation → heap overflow; fix = checked multiply or `calloc` |
| **Crypto primitives** | XOR/Caesar/FNV-1a build intuition for Module 18 — and show key reuse breaks a "one-time" pad |
| **Constant-time compare** | early-exit `memcmp` leaks secrets via timing; constant-time compare is the foundation of side-channel-safe code |

## Further reading

- **CS:APP3e, Chapter 3 — Machine-Level Representation of Programs** (stack frames,
  how an overflow reaches the return address — the definitive treatment):
  http://csapp.cs.cmu.edu/
- **CS:APP Attack Lab** (do a *real* buffer overflow / ROP exercise safely, in the
  course's sandboxed x86-64 binaries): http://csapp.cs.cmu.edu/
- **OWASP** (the canonical catalogue of application vulnerabilities and defences):
  https://owasp.org/
- **MIT 6.5660 — Computer Systems Security** (the systems-security course this module
  sits under): https://css.csail.mit.edu/6.858/
- **"Cryptographic Right Answers"** (Latacora — what to actually use, so you never ship
  the toy primitives above): https://www.latacora.com/blog/2018/04/03/cryptographic-right-answers/

**Next:** Module 44 — C++ for Systems — RAII, references, templates, the STL, smart
pointers and move semantics; rewrite an earlier C lab in modern C++.
*(Not yet built — see [the track plan](../cs-foundations-track.md).)* →
[../44_cpp_for_systems/README.md](../44_cpp_for_systems/README.md)
