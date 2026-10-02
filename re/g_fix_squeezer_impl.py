# -*- coding: utf-8 -*-
"""Update Squeezer's implementation for the corrected declaration, and declare the cost method the source defines.

THE DECLARATION NOW SAYS WHERE THE FIELDS ARE -- inside the 0x270 byte object at +8 -- and the implementation still initialised them as Squeezer's
own. **THE SAME RULE AS EVERYWHERE ELSE IN THIS SESSION: an implementation that disagrees with its declaration is one of the two being wrong, and
here it is the implementation.**
"""
import io
import re
import sys

ROW = r"D:\Nesting\nestfab\lcns\include\lcns\row.hpp"
SRC = r"D:\Nesting\nestfab\lcns\src\row.cpp"

OLD_CTOR = """Squeezer::Squeezer(double twiceMaxExtent, double coeffAt0x18, double thresholdAt0x10)
    : enabled_(true),                       // RE: inner[+8] = 1 (0x138A6B)
      coeff_(coeffAt0x18),                  // RE: inner[+0x00] = xmm2
      threshold_(thresholdAt0x10),          // RE: inner[+0x10] = xmm3
      twiceMaxExtent_(twiceMaxExtent) {}    // RE: 0x2530D0(2 * xmm1, xmm2)"""

NEW_CTOR = """// RE 0x138A20: the constructor installs the vtable, ALLOCATES the 0x270 byte object and stores it at +8, and touches nothing else of the
// Squeezer object. **So the three scalars are initialised in the Impl, not in the handle** -- which is what the declaration now says and what the
// instructions at 0x138A6B, 0x138A72 and 0x138A79 do.
Squeezer::Squeezer(double twiceMaxExtent, double coeffAt0x18, double thresholdAt0x10)
    : impl_(new Impl{true, coeffAt0x18, thresholdAt0x10, twiceMaxExtent}) {}"""


def fix_impl():
    text = io.open(SRC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD_CTOR not in text:
        print("REFUSING: the constructor's initialiser list is not as expected")
        return 2
    text = text.replace(OLD_CTOR, NEW_CTOR, 1)
    io.open(SRC, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote Squeezer's constructor to initialise the Impl")
    return 0


def declare_cost():
    text = io.open(ROW, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "double cost(" in text:
        print("cost is already declared")
        return 0
    marker = "        std::size_t misses() const { return misses_; }"
    if marker not in text:
        print("REFUSING: the insertion point is not found")
        return 2
    text = text.replace(marker, marker + """

        /** The cost of a key, RE 0x13A360 and the routine around it: a cache hit returns the stored value, and a miss computes one. Its body is
         *  in lcns/src/row.cpp beside the instructions. */
        double cost(std::uintptr_t lo, std::uintptr_t hi, const SqueezeContext& ctx);""", 1)
    io.open(ROW, "w", encoding="utf-8", newline="\n").write(text)
    print("declared Squeezer::cost")
    return 0


if __name__ == "__main__":
    code = fix_impl()
    if code == 0:
        code = declare_cost()
    sys.exit(code)
