// Module 43 — Demo 4: Crypto primitives, FOR LEARNING ONLY
//
// White-hat / educational. These are TOY implementations to build intuition for the
// theory under your applied Module 18. They are NOT secure and MUST NOT be used to
// protect anything real — use libsodium or the library from Module 18 instead.
// Build & run with: make run4.  Read alongside README.md §4.
//
// Covered: (a) XOR cipher + why key reuse is fatal, (b) Caesar/ROT shift,
// (c) a tiny checksum-style hash, (d) constant-time compare vs naive memcmp and the
// timing side-channel that motivates it (ties to Module 18).

#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stddef.h>

// --- (a) XOR cipher ---------------------------------------------------------
// c[i] = p[i] ^ key[i % keylen]. Symmetric: the same op decrypts. TOY ONLY.
static void xor_crypt(unsigned char *out, const unsigned char *in, size_t n,
                      const unsigned char *key, size_t keylen) {
    for (size_t i = 0; i < n; i++) out[i] = in[i] ^ key[i % keylen];
}

// --- (b) Caesar / ROT shift on letters -------------------------------------
static void caesar(char *out, const char *in, int shift) {
    for (size_t i = 0; in[i]; i++) {
        char ch = in[i];
        if (ch >= 'a' && ch <= 'z')      out[i] = (char)('a' + (ch - 'a' + shift + 26) % 26);
        else if (ch >= 'A' && ch <= 'Z') out[i] = (char)('A' + (ch - 'A' + shift + 26) % 26);
        else                             out[i] = ch;
    }
    out[strlen(in)] = '\0';
}

// --- (c) Tiny checksum-style hash (FNV-1a, 32-bit) -------------------------
// A real, simple non-cryptographic hash. Good for hash tables; NOT a secure digest
// (no collision resistance vs an adversary). For real hashing use SHA-256/BLAKE2.
static uint32_t fnv1a(const unsigned char *data, size_t n) {
    uint32_t h = 2166136261u;            // FNV offset basis
    for (size_t i = 0; i < n; i++) {
        h ^= data[i];
        h *= 16777619u;                  // FNV prime
    }
    return h;
}

// --- (d) Naive vs constant-time comparison ---------------------------------
// NAIVE: returns as soon as a byte differs — its running time leaks HOW MANY leading
// bytes matched, so an attacker can recover a secret (e.g. an HMAC tag) byte by byte.
static int compare_naive(const unsigned char *a, const unsigned char *b, size_t n) {
    for (size_t i = 0; i < n; i++) {
        if (a[i] != b[i]) return 0;      // early exit: timing depends on the data
    }
    return 1;
}

// CONSTANT-TIME: always touches every byte; the time does not depend on where (or
// whether) they differ. OR-accumulate the per-byte differences, branch only at the end.
static int compare_constant_time(const unsigned char *a, const unsigned char *b, size_t n) {
    unsigned char diff = 0;
    for (size_t i = 0; i < n; i++) {
        diff |= (unsigned char)(a[i] ^ b[i]);   // 0 only if every byte matched
    }
    return diff == 0;
}

static void print_hex(const char *label, const unsigned char *d, size_t n) {
    printf("%s", label);
    for (size_t i = 0; i < n; i++) printf("%02x", d[i]);
    putchar('\n');
}

int main(void) {
    printf("=== Toy crypto primitives — FOR LEARNING ONLY, never production ===\n\n");

    // (a) XOR cipher round-trip
    const unsigned char key[] = { 0x9f, 0x2c, 0x71 };
    const unsigned char msg[] = "attack at dawn";
    size_t mlen = sizeof msg - 1;                 // drop the trailing NUL
    unsigned char ct[64], rt[64];
    xor_crypt(ct, msg, mlen, key, sizeof key);
    xor_crypt(rt, ct, mlen, key, sizeof key);
    printf("(a) XOR cipher\n");
    print_hex("    plaintext : ", msg, mlen);
    print_hex("    ciphertext: ", ct, mlen);
    print_hex("    decrypted : ", rt, mlen);

    // Key-reuse weakness: c1 ^ c2 == p1 ^ p2 (the key cancels). Encrypting two
    // messages under the SAME keystream leaks their XOR — a classic break.
    const unsigned char m1[] = "HELLO";
    const unsigned char m2[] = "WORLD";
    unsigned char c1[8], c2[8], xc[8], xp[8];
    xor_crypt(c1, m1, 5, key, sizeof key);
    xor_crypt(c2, m2, 5, key, sizeof key);        // same key -> same keystream
    for (size_t i = 0; i < 5; i++) {
        xc[i] = c1[i] ^ c2[i];
        xp[i] = m1[i] ^ m2[i];
    }
    printf("    key reuse: c1^c2 == p1^p2 ? %s  (the key cancels -> info leak)\n",
           memcmp(xc, xp, 5) == 0 ? "yes" : "no");

    // (b) Caesar / ROT
    char enc[64], dec[64];
    caesar(enc, "Hello, ROT-3!", 3);
    caesar(dec, enc, -3);
    printf("\n(b) Caesar shift (+3)\n    \"Hello, ROT-3!\" -> \"%s\" -> \"%s\"\n", enc, dec);

    // (c) FNV-1a checksum
    printf("\n(c) FNV-1a hash (non-cryptographic)\n");
    printf("    fnv1a(\"hello\") = 0x%08x\n", fnv1a((const unsigned char *)"hello", 5));
    printf("    fnv1a(\"hellp\") = 0x%08x  (one byte changed)\n",
           fnv1a((const unsigned char *)"hellp", 5));

    // (d) Constant-time comparison
    printf("\n(d) Tag comparison: naive vs constant-time\n");
    unsigned char expected[] = { 0xde, 0xad, 0xbe, 0xef, 0x00, 0x11 };
    unsigned char guess_ok[]  = { 0xde, 0xad, 0xbe, 0xef, 0x00, 0x11 };
    unsigned char guess_bad[] = { 0xde, 0xad, 0x00, 0x00, 0x00, 0x00 };
    size_t tlen = sizeof expected;
    printf("    naive(correct)        = %d   constant_time(correct)        = %d\n",
           compare_naive(expected, guess_ok, tlen),
           compare_constant_time(expected, guess_ok, tlen));
    printf("    naive(wrong)          = %d   constant_time(wrong)          = %d\n",
           compare_naive(expected, guess_bad, tlen),
           compare_constant_time(expected, guess_bad, tlen));
    printf("    naive returns early on the first mismatch -> its TIMING leaks how many\n");
    printf("    leading bytes were right. Always compare secrets in constant time.\n");

    printf("\nFor real use: libsodium, or the cryptography library from Module 18.\n");
    return 0;
}
