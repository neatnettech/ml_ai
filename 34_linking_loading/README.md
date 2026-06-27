# Module 34 — Linking, Loading & Processes

**Purpose:** You write `hello.c`; you run `./hello`. In between, four tools turn
source into machine code and a fifth program — the *loader* — turns that file into a
live process. Module 31 introduced multi-file builds and the linker in passing; this
module follows the whole pipeline end to end: the four compiler **stages**
(preprocess → compile → assemble → link), the difference between **static** and
**dynamic** libraries, how the linker and loader do **symbol resolution**, and the
**process** that finally results. These are the mechanics every later systems module
(virtual memory, the kernel) takes for granted.

**Prerequisites:** Module 31 (multi-file C, headers vs source, the `Makefile`
two-step build, what the linker does at a high level). Module 28 helps for reading
hex/bytes but isn't required.

**What you'll learn:**
- The **four build stages** and the artifact each one produces (`.i`, `.s`, `.o`, exe)
- **Static libraries** (`ar` archives, `.a`): symbols are *copied* into your binary
- **Dynamic libraries** (`.dylib`/`.so`): symbols are *bound at load time* by the
  dynamic loader (**dyld** on macOS, **ld.so** on Linux)
- **Symbol resolution**: defined (`T`) vs imported/undefined (`U`), and how to read
  the famous *"Undefined symbols"* linker error
- **Linkage**: `static` (internal, private to a translation unit) vs `extern`/file
  scope (external, visible to the linker)
- Inspecting binaries with **`nm`** and **`otool`** (Linux: `readelf`, `ldd`)

> **Format:** this track is real C, not notebooks. Each module is source files + a
> `Makefile` + this lab. Build everything with `make`, run a demo with `make run1`,
> attempt an exercise in `exercises/`, check against `solutions/`.

## Setup

Module 34 builds and runs **natively on Apple Silicon** — just `clang` + `make`
(Xcode Command Line Tools). The native object/executable format here is **Mach-O**
and the run-time loader is **dyld**; the inspection tools are `nm`, `otool`, and the
`clang` driver flags `-E/-S/-c`.

```bash
make run        # build + run all four demos (incl. the dynamic-lib demo)
make symbols    # nm / otool inspection of the built binaries
```

**Linux / ELF notes (for the x86-64 container).** On Linux the object/executable
format is **ELF**, the loader is **ld.so**, shared libraries end in **`.so`** (built
with `-shared -fPIC`), and you inspect with **`readelf -s`** / **`nm`** for symbols
and **`ldd`** for shared-library dependencies. The concepts are identical; only the
file format and tool names differ. Each section below gives the Linux equivalent.
To run those commands, use the x86-64 Linux container from Module 28's
[`setup/README.md`](../28_bits_and_bytes/setup/README.md).

---

## 1. The four stages: `.c` → `.i` → `.s` → `.o` → executable

`clang hello.c -o hello` looks like one step, but the driver runs four. Each `clang`
flag stops the pipeline at a different artifact, all captured by `make run1`:

| Stage | Flag | Tool | Output | What happens |
|-------|------|------|--------|--------------|
| Preprocess | `-E` | preprocessor | `hello.i` | `#include` pasted in, `#define` expanded |
| Compile | `-S` | compiler | `hello.s` | C → architecture assembly |
| Assemble | `-c` | assembler | `hello.o` | assembly → **Mach-O object** (code + symbols) |
| Link | *(none)* | linker (`ld`) | `hello` | objects + libraries → **executable** |

```
make run1
```
```
── demo 1: the four build stages on hello.c ──
[1] preprocessed (bin/hello.i): macro + #include expanded — last lines:
    int main(void) {
        puts("hello, linker");
        return 0;
    }
[2] assembly (bin/hello.s): the call to puts — grep:
    	bl	_puts
[3] object (bin/hello.o): Mach-O, symbol table —
    bin/hello.o: Mach-O 64-bit object arm64
[4] linked executable runs:
    hello, linker
```

Note the macro `GREETING` is *gone* by stage 1 — it became the literal string. The
assembly calls `_puts` (Mach-O prefixes C names with `_`); the object is **Mach-O**;
only the final link produces something dyld can run. On Linux the object would be
*ELF 64-bit relocatable* and the assembly call `call puts@PLT`.

## 2. Static libraries — symbols copied in (`libmymath.a`)

A **static library** is just an archive of `.o` files made with `ar rcs`. At link
time the linker pulls the members you actually reference *into* your executable, then
the archive is no longer needed. [`mymath.c`](mymath.c)/[`mymath.h`](mymath.h) become
`libmymath.a`, and [`02_use_static.c`](02_use_static.c) links it (`make run2`):

```
clang -c mymath.c -o bin/mymath.o          # defines _mm_gcd, _mm_ipow
ar rcs bin/libmymath.a bin/mymath.o        # archive them
clang 02_use_static.c -Lbin -lmymath -o bin/02_use_static   # copy them in
```
```
── demo 2: static library (libmymath.a) ──
static lib demo
  mm_gcd(48, 36) = 12
  mm_ipow(2, 10) = 1024
```

`nm` on the archive shows the members and the symbols each defines (`T` = text/code,
defined). From `make symbols`:

```
── nm libmymath.a ──
mymath.o:
0000000000000000 T _mm_gcd
0000000000000094 T _mm_ipow
```

After the static link, those symbols are **defined inside the executable itself**:

```
── nm bin/02_use_static  (static: mm_gcd is T = DEFINED in the binary) ──
0000000100000460 T _main
00000001000004d8 T _mm_gcd
000000010000056c T _mm_ipow
```

Linux/ELF: identical workflow — `ar rcs libmymath.a mymath.o`, then `nm` shows the
same `T`/`U` letters (the letter scheme is shared between ELF and Mach-O `nm`).

## 3. Dynamic libraries — bound at load time by dyld (`libmymath.dylib`)

A **dynamic (shared) library** is *not* copied in. The linker only records "I depend
on `libmymath.dylib`, and I need `mm_gcd`/`mm_ipow` from it." At **run time**, the
dynamic loader **dyld** maps the library into the process and binds the symbols.
[`03_use_dynamic.c`](03_use_dynamic.c) links the `.dylib` (`make run3`):

```
clang -dynamiclib -install_name @rpath/libmymath.dylib mymath.c -o bin/libmymath.dylib
clang 03_use_dynamic.c -Lbin -lmymath -Wl,-rpath,@loader_path -o bin/03_use_dynamic
```
```
── demo 3: dynamic library (libmymath.dylib via dyld) ──
dynamic lib demo
  mm_gcd(1071, 462) = 21
  mm_ipow(3, 4)     = 81
```

The two macOS-specific flags are what make this *run* without any `DYLD_*`
environment variable:
- **`-install_name @rpath/libmymath.dylib`** stamps the library's own name as
  "find me via the client's rpath," rather than an absolute build path.
- **`-Wl,-rpath,@loader_path`** tells the executable to look for its libraries in its
  own directory (`@loader_path` = the folder the binary loaded from — here `bin/`,
  where the `.dylib` also lives).

Now `nm` shows `mm_gcd`/`mm_ipow` as **`U` (undefined/imported)** — they live in the
`.dylib`, not the executable — and `otool -L` lists the run-time dependencies:

```
── nm bin/03_use_dynamic (dynamic: mm_gcd is U = imported) ──
0000000100000460 T _main
                 U _mm_gcd
                 U _mm_ipow

── otool -L bin/03_use_dynamic ──
bin/03_use_dynamic:
	@rpath/libmymath.dylib (compatibility version 0.0.0, current version 0.0.0)
	/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1356.0.0)
```

That `libSystem.B.dylib` is where macOS keeps the C library (so `printf` etc. are
*always* dynamically loaded). Compare demo 2 (`mm_gcd` is `T`) with demo 3 (`mm_gcd`
is `U`): same source, different *when* the symbol is resolved — link time vs load
time.

Linux/ELF: `clang -shared -fPIC -o libmymath.so mymath.c`; link with
`-L. -lmymath -Wl,-rpath,'$ORIGIN'` (`$ORIGIN` is the ELF analogue of
`@loader_path`); inspect run-time deps with **`ldd ./03_use_dynamic`** (which would
list `libmymath.so` and `libc.so.6`).

## 4. Linkage — `static` (internal) vs `extern` (external)

**Linkage** decides whether a name in one `.c` file refers to the same entity as a
name in another. The linker only ever sees **external** linkage; **internal**
(`static` at file scope) names are private to their translation unit and never reach
the linker's symbol table. [`04_linkage.c`](04_linkage.c) + [`04_helper.c`](04_helper.c)
are two TUs linked together (`make run4`):

```
── demo 4: internal vs external linkage ──
internal vs external linkage
  before: g_shared_counter = 0
  after main++ and helper_bump(): g_shared_counter = 2
  this file's secret(): main.c's private secret
  helper's  secret(): helper.c's private secret
```

- **`g_shared_counter`** is a file-scope variable with **external** linkage. The
  helper reaches it via `extern int g_shared_counter;` — both files touch the **same**
  object, so it ends at `2`.
- **`secret()`** is `static` (internal) in *both* files. There are two functions
  named `secret`, one per TU, and **no duplicate-symbol error** — because neither name
  is visible to the linker.

Two errors worth recognizing (explained, not built by default):
- **Undefined symbol** — you call/declare a name nothing defines. This is Exercise
  34.2; the message is dissected in §6.
- **Duplicate symbol** — two TUs define the *same* external name. If you *removed*
  `static` from both `secret()`, the linker would abort with
  `duplicate symbol '_secret'`. The fix is `static` (make it internal) or define it
  once and share via a header. (Linux/ELF wording: `multiple definition of 'secret'`.)

---

## 5. Inspecting binaries: `nm` and `otool`

`make symbols` runs the inspection tools over the demo binaries. The vocabulary:

| Tool (macOS) | Linux equivalent | Shows |
|--------------|------------------|-------|
| `nm file` | `nm` / `readelf -s` | symbol table; `T`=defined text, `U`=undefined/imported |
| `otool -L file` | `ldd file` | shared libraries loaded at run time |
| `otool -hv file` | `readelf -h` | the Mach-O / ELF header |

The letter you care about most is **`U`**: it means "this binary uses a symbol it does
not contain — something else must supply it," whether a `.dylib` at load time or
another `.o` at link time.

---

## 6. Exercises

Each lives in `exercises/` with a `// TODO`; a reference answer is in `solutions/`.
Build & run your attempt with `make exN`, the solution with `make solN`.

### Exercise 34.1 — Split a program into a library  (`make ex1`)
[`exercises/ex1_celsius.c`](exercises/ex1_celsius.c) is a single-file program with the
conversion function jammed next to `main`. Move the function into a library
([`ex1_celsius_lib.c`](exercises/ex1_celsius_lib.c) + [`ex1_celsius.h`](exercises/ex1_celsius.h),
archived into `libtemp.a`) and leave `main` to only *declare* (via the header) and
*call* it. Expected (`make sol1`):
```
     0.0 C =   32.0 F
    37.0 C =   98.6 F
   100.0 C =  212.0 F
```

### Exercise 34.2 — Trigger and fix an "undefined symbol" error  (`make ex2`)
[`exercises/ex2_undefined.c`](exercises/ex2_undefined.c) declares and calls `triple`
but never defines it, so `make ex2` is **expected to fail** at the link step:
```
── ex2: this link is SUPPOSED to fail (undefined symbol) ──
Undefined symbols for architecture arm64:
  "_triple", referenced from:
      _main in ex2_undefined-1f8c83.o
ld: symbol(s) not found for architecture arm64
clang: error: linker command failed with exit code 1
```
How to read it: the symbol is **`_triple`** (Mach-O underscore prefix), it was
**referenced from `_main`**, and `ld` couldn't find a definition. The fix is to
*define* `triple`. The fixed version is [`solutions/ex2_undefined.c`](solutions/ex2_undefined.c)
(`make sol2` → `triple(7) = 21`). On Linux the same mistake reads
`undefined reference to 'triple'`.

### Exercise 34.3 — Read a binary's symbols with `nm` / `otool`  (`make ex3`)
[`exercises/ex3_symbols.c`](exercises/ex3_symbols.c) defines `my_square` and calls
`printf` (which it does not define). `make ex3` builds it and dumps `nm` + `otool -L`;
identify which symbol is defined vs imported, and which dylib supplies `printf`:
```
── nm (T = defined here, U = imported) ──
0000000100000460 T _my_square     <- defined in this binary
                 U _printf         <- imported from the C library
── otool -L (shared libraries) ──
	/usr/lib/libSystem.B.dylib     <- supplies printf at run time
```

---

## What you learned

| Concept | Why it matters |
|---------|----------------|
| **The four stages** (`-E/-S/-c`/link) | `clang` is a driver over preprocessor, compiler, assembler, linker — each artifact is inspectable |
| **Static libraries** (`.a`, `ar`) | Members are *copied* into the executable at link time → symbols become `T` (defined) inside it |
| **Dynamic libraries** (`.dylib`/`.so`) | Symbols stay `U` (imported) and are bound at *load* time by dyld/ld.so → smaller binaries, shared code, but a run-time dependency |
| **Symbol resolution** | `T` vs `U` in `nm`, the "Undefined symbols" / "undefined reference" error, and the duplicate-symbol error |
| **Linkage** (`static` vs `extern`) | Internal linkage hides a name from the linker; external linkage is what lets (and forces) TUs agree on names |
| **`nm` / `otool` (`readelf` / `ldd`)** | Read any binary's symbol table and library dependencies — the diagnostic skill behind every link error |

## Further reading

- **CS:APP3e, Chapter 7 — Linking** (the definitive treatment; pairs with this
  module 1:1): http://csapp.cs.cmu.edu/
- **"Linkers and Loaders"** by John R. Levine — the book-length tour of archives,
  relocation, shared objects, and dynamic loading.
- **`man dyld`** and Apple's *Dynamic Library Programming Topics* — the macOS loader,
  `@rpath`/`@loader_path`/`@executable_path`, and install names.
- For the Linux/ELF side: **`man ld.so`**, **`man readelf`**, and CS:APP §7.12 on
  position-independent code and dynamic linking.

**Next:** Module 35 — Virtual Memory & Allocation — address translation, paging,
`mmap`, and writing your own `malloc`/`free` (CS:APP ch.9 + Malloc Lab). *(Not yet
built — see [the track plan](../cs-foundations-track.md).)* → ../35_virtual_memory/README.md
