# -*- coding: utf-8 -*-
"""Correct Order's +0x1F8..+0x208 range from the three exports that write it, and add the two fields it lacks.

**THE EVIDENCE IS THREE EXPORTS AND IT SETTLES FOUR FIELDS, ONE OF WHICH ORDER DOES NOT HAVE AT ALL.**

    SetLocalEngine         0xD370   mov byte [rsi + 0x200], al     ; the complement of the low bit
                                    mov byte [rsi + 0x201], bl     ; the complement of bit one
    SetLocalEngineThreads  0xDE80   mov dword [rdi + 0x204], r12d
                                    mov dword [rdi + 0x208], ebp
    and lcns/src/exports_impl.cpp already reads 0xD38B, 0xD389, 0xD390 and 0xD3A0 into a `LocalEngineCarrier`:
        std::uint32_t maxThreads;   // +0x1F8, RE 0xD3D5 and RE 0xD3E7
        unsigned char engineLo;     // +0x200, RE 0xD390
        unsigned char engineHi;     // +0x201, RE 0xD3A0

**SO THE WIDTHS OF THE WHOLE RANGE ARE PINNED BY INSTRUCTIONS:**

    +0x1F8   4 bytes   `mov dword [rsi], eax` at 0xD3D5 and 0xD3E7  -> `maxThreads` is CONFIRMED, and it matches
    +0x1FC   4 bytes   and the next CONFIRMED field is two bytes away at +0x200, and the one after that at +0x204
    +0x200   1 byte    RE 0xD390
    +0x201   1 byte    RE 0xD3A0
    +0x202   2 bytes   NOT WRITTEN BY ANY OF THE THREE, so nothing establishes them
    +0x204   4 bytes   `mov dword [rdi + 0x204], r12d` at 0xDF73  -> **ORDER DOES NOT DECLARE THIS**
    +0x208   4 bytes   `mov dword [rdi + 0x208], ebp` at 0xDF7A   -> **ORDER DOES NOT DECLARE THIS EITHER**

**AND `Order`'s `bool localEngine` AT +0x200 IS A ONE BYTE FIELD WITH A THREE BYTE GAP AFTER IT**, which `localEngine` cannot be: the module stores ONE byte
there and the next field is at +0x204. **So the declaration is not wrong about WHERE it is and is wrong about how much of the range it accounts for.**
"""
import io
import re
import sys

MODEL = r"D:\Nesting\nestfab\lcns\include\lcns\model.hpp"

OLD = """    int maxThreads = 1;   // +0x1F8
    int maxIterations = 1000;   // +0x1FC
    bool localEngine = false;   // +0x200"""

NEW = """    /** **THE +0x1F8..+0x208 RANGE, FROM THREE EXPORTS.** `SetLocalEngine` at 0xD370 is `mov byte [rsi + 0x200], al` and `mov byte [rsi + 0x201], bl`;
     *  `SetLocalEngineThreads` at 0xDE80 is `mov dword [rdi + 0x204], r12d` and `mov dword [rdi + 0x208], ebp`; and `exports_impl.cpp` already reads 0xD3D5,
     *  0xD3E7, 0xD390 and 0xD3A0 into a `LocalEngineCarrier` whose fields are `maxThreads` at +0x1F8, `engineLo` at +0x200 and `engineHi` at +0x201.
     *
     *  **SO THE WIDTHS ARE PINNED BY INSTRUCTIONS RATHER THAN BY THE DECLARATION**: four bytes at +0x1F8, one byte at +0x200, one at +0x201, **two bytes at
     *  +0x202 that NO export writes and that nothing therefore establishes**, and four bytes each at +0x204 and +0x208. */
    std::uint32_t maxThreads = 1;        // +0x1F8, RE 0xD3D5 and RE 0xD3E7: mov dword [rsi], eax
    std::uint32_t maxIterations = 1000;  // +0x1FC, between a CONFIRMED four byte field and a CONFIRMED one byte field two bytes later
    std::uint8_t engineLo = 0;           // +0x200, RE 0xD390: mov byte [rsi + 0x200], al -- the COMPLEMENT of the argument's low bit
    std::uint8_t engineHi = 0;           // +0x201, RE 0xD3A0: mov byte [rsi + 0x201], bl -- the complement of bit one
    std::byte unestablished202[0x2];     // +0x202..+0x203: **NO EXPORT WRITES THIS**, so it is padded rather than named
    std::uint32_t threadsA = 0;          // +0x204, RE 0xDF73: mov dword [rdi + 0x204], r12d -- **the module writes it and Order did NOT declare it**
    std::uint32_t threadsB = 0;          // +0x208, RE 0xDF7A: mov dword [rdi + 0x208], ebp  -- and the same"""


def main():
    text = io.open(MODEL, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "THE +0x1F8..+0x208 RANGE, FROM THREE EXPORTS" in text:
        print("the range is already corrected")
        return 0
    if OLD not in text:
        print("REFUSING: the three declarations are not as expected")
        for line in text.split("\n"):
            if "maxThreads" in line or "localEngine" in line:
                print("   found: %s" % line.strip()[:96])
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(MODEL, "w", encoding="utf-8", newline="\n").write(text)
    print("corrected the range: maxThreads and maxIterations confirmed, localEngine split into engineLo/engineHi,")
    print("  +0x202 padded as unestablished, and +0x204/+0x208 added")
    return 0


if __name__ == "__main__":
    sys.exit(main())
