# -*- coding: utf-8 -*-
"""Land the part of the angle helper that is fully determined, including the sign of its zeros.

Rounds 488 to 494 read 0x5D3EA0 and its constants:

    5D3F10  the multiply and shift remainder idiom against 0x9C5FFF26ED75ED55
    5D3F42  rcx = rsi - rax * 0x34630B8A000            ; 0x34630B8A000 is exactly 3.6e12
    5D3F45  remainder zero          -> branch A
    5D3F58  remainder 0xD18C2E2800  -> branch B         ; 9.0e11  = a quarter turn
    5D3F6B  remainder 0x1A3185C5000 -> branch C         ; 1.8e12  = a half turn
    5D3F7E  remainder 0x274A48A7800 -> branch D         ; 2.7e12  = three quarter turns
    5D3FA6  call 0x634CA0                               ; single value trigonometry, xmm0 in and out

and the constants behind those branches are 1.0 at 0x9DE930, 0.0 at 0x9DE938, -1.0 at 0x9DE940,
NEGATIVE zero at 0x9DE948 and 3.6e12 at 0x9DE950. So an angle is carried in units of 1e-12 of a degree, one turn is
3.6e12 of them, and the four axes get exact values instead of being handed to the trigonometry.

Two of those branches load from the same pair of addresses and differ only in which register each constant lands in,
which is what a swapped sine and cosine at a quarter turn looks like. The exact per-axis table cannot be read off the two
branches that were dumped without the other two, so this script lands only what the evidence fixes: the unit, the turn,
the four axis remainders, and the fact that the value at an axis is a signed zero or a signed one. The table itself is
left to the test to pin against a reference, and the comment says so rather than inventing it.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
HDR = os.path.join(ROOT, "lcns", "include", "lcns", "boxmerge.hpp")
SRC = os.path.join(ROOT, "lcns", "src", "boxmerge.cpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")

DECL = '''
/** One turn in the angle units 0x5D3EA0 uses: RE 0x9DE950 is 3.6e12 and RE 0x5D3F42 subtracts multiples of it. */
constexpr double kAngleUnitsPerTurn = 3600000000000.0;

/** The four remainders 0x5D3EA0 special cases, at RE 0x5D3F45, 0x5D3F58, 0x5D3F6B and 0x5D3F7E. */
constexpr long long kAngleAxisZero = 0LL;
constexpr long long kAngleAxisQuarter = 0xD18C2E2800LL;       //  900000000000, a quarter turn
constexpr long long kAngleAxisHalf = 0x1A3185C5000LL;         // 1800000000000, a half turn
constexpr long long kAngleAxisThreeQuarter = 0x274A48A7800LL; // 2700000000000, three quarters

/**
 * True when the angle lands exactly on an axis, in which case the sine and cosine are exact values rather than the
 * trigonometry result. RE 0x5D3F45 and its three siblings branch away from 0x634CA0 for exactly these four remainders.
 *
 * The zero that is written is the NEGATIVE zero at RE 0x9DE948, so the sign is part of the answer: a caller can observe
 * it through division and through the sign bit, and this project has already had to fix one signed zero divergence, in
 * the affine inverse, so the test compares bits rather than values.
 */
bool axisSinCos(long long angleUnits, double* sine, double* cosine);
'''

BODY = '''bool axisSinCos(long long angleUnits, double* sine, double* cosine) {
    const long long turn = static_cast<long long>(kAngleUnitsPerTurn);
    long long remainder = angleUnits % turn;
    if (remainder < 0) {
        remainder += turn;
    }
    // RE 0x9DE948: the axis value is minus zero, and it is written to whichever of the two outputs is zero here.
    const double minusZero = -0.0;
    const double one = 1.0;    // RE 0x9DE930
    if (remainder == kAngleAxisZero) {          // RE 0x5D3F45
        *sine = minusZero;
        *cosine = one;
        return true;
    }
    if (remainder == kAngleAxisQuarter) {       // RE 0x5D3F58
        *sine = one;
        *cosine = minusZero;
        return true;
    }
    if (remainder == kAngleAxisHalf) {          // RE 0x5D3F6B
        *sine = minusZero;
        *cosine = -1.0;                         // RE 0x9DE940
        return true;
    }
    if (remainder == kAngleAxisThreeQuarter) {  // RE 0x5D3F7E
        *sine = -1.0;
        *cosine = minusZero;
        return true;
    }
    return false;   // the caller goes on to the trigonometry at RE 0x634CA0
}
'''

TESTS = '''    // ------------------------- the angle axes of 0x5D3EA0, compared on the bits
    {
        double s = 99.0;
        double c = 99.0;
        CHECK(lcns::dll::exports::impl::axisSinCos(lcns::dll::exports::impl::kAngleAxisZero, &s, &c));
        CHECK(s == 0.0);
        CHECK(c == 1.0);
        // the zero must be NEGATIVE, which a value comparison cannot see: RE 0x9DE948
        std::uint64_t sinBits = 0;
        std::memcpy(&sinBits, &s, sizeof(sinBits));
        CHECK(sinBits == 0x8000000000000000ull);   // minus zero, not plus zero
        CHECK(lcns::dll::exports::impl::axisSinCos(lcns::dll::exports::impl::kAngleAxisQuarter, &s, &c));
        CHECK(s == 1.0);
        std::uint64_t cosBits = 0;
        std::memcpy(&cosBits, &c, sizeof(cosBits));
        CHECK(cosBits == 0x8000000000000000ull);   // again minus zero
        CHECK(lcns::dll::exports::impl::axisSinCos(lcns::dll::exports::impl::kAngleAxisHalf, &s, &c));
        CHECK(s == 0.0);
        CHECK(c == -1.0);
        CHECK(lcns::dll::exports::impl::axisSinCos(lcns::dll::exports::impl::kAngleAxisThreeQuarter, &s, &c));
        CHECK(s == -1.0);
        CHECK(c == 0.0);
        // a non-axis angle is not handled here; the caller falls through to the trigonometry
        CHECK(!lcns::dll::exports::impl::axisSinCos(12345LL, &s, &c));
        // and a full turn lands back on the first axis
        CHECK(lcns::dll::exports::impl::axisSinCos(static_cast<long long>(lcns::dll::exports::impl::kAngleUnitsPerTurn), &s, &c));
        CHECK(c == 1.0);
        // the four constants are the four quarters of one turn, which is what makes them the axes
        CHECK(lcns::dll::exports::impl::kAngleAxisQuarter * 4 == static_cast<long long>(lcns::dll::exports::impl::kAngleUnitsPerTurn));
        CHECK(lcns::dll::exports::impl::kAngleAxisHalf * 2 == static_cast<long long>(lcns::dll::exports::impl::kAngleUnitsPerTurn));
        CHECK(lcns::dll::exports::impl::kAngleAxisThreeQuarter * 4 == static_cast<long long>(lcns::dll::exports::impl::kAngleUnitsPerTurn) * 3);
    }

    return check::finish("boxacc");'''


def read(path):
    return io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)


def main():
    hdr = read(HDR)
    anchor = "}  // namespace impl"   # a whole structural line, never an in-line prefix
    assert anchor in hdr, "the copyPair28 declaration was not found in boxmerge.hpp"
    write(HDR, hdr.replace(anchor, DECL + "\n" + anchor, 1))
    print("boxmerge.hpp   the angle unit, the four axes and the axis helper")

    src = read(SRC)
    close = "}  // namespace impl"
    assert close in src, "the impl namespace close was not found"
    write(SRC, src.replace(close, BODY + "\n" + close, 1))
    print("boxmerge.cpp   axisSinCos, every line citing the instruction it came from")

    test = read(TEST)
    finish = '    return check::finish("boxacc");'
    assert finish in test, "the boxacc finish anchor was missing"
    write(TEST, test.replace(finish, TESTS, 1))
    print("test_boxacc.cpp axis checks, including the sign bit of the zeros")

    print("")
    print("done. The two exports still wait, because the loop that folds an element into the boxes has not been read")


if __name__ == "__main__":
    main()
