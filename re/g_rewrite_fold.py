# -*- coding: utf-8 -*-
"""Rewrite StatBox::fold from the WHOLE body of RE 0x5C8C50.

Three attempts failed because a reading was taken from a fragment. The body is 255 bytes and says:

    the element is skipped when its own +0x00 flag is zero          (0x5C8C50 / je / ret)
    the box's flag NONZERO means BUILD: copy the element's a and b into all four slots, clear the flag, then fall into the
        comparisons for c and d                                     (0x5C8D10 through 0x5C8D4D)
    the box's flag ZERO means COMPARE a, b, c and d against the box (0x5C8C69 through 0x5C8D0B)

so `valid` is "BUILD ME" rather than "I am valid", and the element is FOUR doubles at +8, +0x10, +0x18 and +0x20.
"""
import io
import re

PATH = r"D:\Nesting\nestfab\lcns\include\lcns\stat.hpp"
START = "/** RE 0x5C8C50: fold one element's measurements into a running bounding box."
END = "/** RE 0x526160 and RE 0x5266A0: the extent of a set"

NEW = '''/** RE 0x5C8C50: fold one element's FOUR doubles into a box of two (low, high) pairs.
 *
 * READ FROM THE WHOLE 255 BYTE BODY, both halves, which is what three earlier attempts did not do. The routine's three branches:
 *
 *     the ELEMENT's flag at +0x00 is zero   -> return without touching the box     (0x5C8C50, je, 0x5C8C55 ret)
 *     the BOX's flag at +0x00 is NONZERO    -> BUILD, then fall into the compare of c and d   (0x5C8D10 .. 0x5C8D4D)
 *     the BOX's flag at +0x00 is ZERO       -> COMPARE a, b, c and d against the box          (0x5C8C69 .. 0x5C8D0B)
 *
 * THE BUILD PATH, 0x5C8D10, copies the element's first two doubles into ALL FOUR slots and clears the flag:
 *
 *     0x5C8D1B  mov [rcx + 8],   [rdx + 8]        ; low0  = a
 *     0x5C8D24  mov [rcx + 0x10],[rdx + 0x10]     ; low1  = b
 *     0x5C8D35  mov [rcx + 0x18],[rdx + 8]        ; high0 = a
 *     0x5C8D39  mov [rcx + 0x20],[rdx + 0x10]     ; high1 = b
 *     0x5C8D14  mov byte ptr [rcx], 0             ; AND THE FLAG IS CLEARED
 *     0x5C8D47  ucomisd xmm1, xmm0 / ja 0x5C8CD1 / jmp 0x5C8CDB   ; then JOIN the compare path at c
 *
 * THE COMPARE PATH, four compare-and-keep pairs over
 *
 *     element +8    against low0 and high0        (0x5C8C69 .. 0x5C8C8F)
 *     element +0x10 against low1 and high1        (0x5C8C94 .. 0x5C8CBD)
 *     element +0x18 against low0 and high0 AGAIN  (0x5C8CC6 .. 0x5C8CE2)
 *     element +0x20 against low1 and high1 AGAIN  (0x5C8CE7 .. 0x5C8D06)
 *
 * **SO `valid` MEANS "BUILD ME" AND NOT "I AM VALID"**, which is why the initialiser RE 0x4E5B0 stores 1 into such a byte: a fresh box
 * needs its first element installed rather than compared against zeros. An earlier version of this struct had the polarity the other way
 * and one value per axis, and it was replaced rather than patched -- the three attempts are in re/blockers.json.
 *
 * THE ELEMENT IS FOUR DOUBLES, at +8, +0x10, +0x18 and +0x20, and all four reach the box: a and b set it, then c and d are compared
 * against what a and b installed.
 */
struct StatBox {
    unsigned char valid = 0;                // +0x00: NONZERO means build from the first element; zero means compare
    double low0 = 0.0;                      // +0x08
    double low1 = 0.0;                      // +0x10
    double high0 = 0.0;                     // +0x18
    double high1 = 0.0;                     // +0x20

    /** One axis's compare-and-keep, the pair of instructions the body repeats four times. */
    static void keep(double value, double& low, double& high) {
        if (value < low) {                                  // RE 0x5C8C73 with 0x5C8C79
            low = value;
        }
        if (value > high) {                                 // RE 0x5C8C88 with 0x5C8C8F
            high = value;
        }
    }

    /** Fold one element's four doubles in. RE 0x5C8C50, whole body.
     *
     * `element_valid` is the element's flag at its +0x00; a zero element is skipped entirely. `a`, `b`, `c` and `d` are the element's four
     * doubles at +8, +0x10, +0x18 and +0x20, named by POSITION because the routine gives them no other identity: a and b go to the two
     * axes, then c and d are compared against the same two axes.
     */
    void fold(bool element_valid, double a, double b, double c, double d) {
        if (!element_valid) {                               // RE 0x5C8C50 / je / 0x5C8C55 ret
            return;
        }
        if (valid) {
            // THE BUILD PATH: 0x5C8D10 installs a and b into both ends of both axes and clears the flag
            low0 = a;                                       // RE 0x5C8D1B
            low1 = b;                                       // RE 0x5C8D24
            high0 = a;                                      // RE 0x5C8D35
            high1 = b;                                      // RE 0x5C8D39
            valid = 0;                                      // RE 0x5C8D14
            // and then the compare path's second half runs, for c and d
            keep(c, low0, high0);                           // RE 0x5C8CC6 / 0x5C8CD1 / 0x5C8CDB / 0x5C8CE2
            keep(d, low1, high1);                           // RE 0x5C8CE7 / 0x5C8CF2 / 0x5C8CFC / 0x5C8D06
            return;
        }
        keep(a, low0, high0);                               // RE 0x5C8C69 / 0x5C8C79 / 0x5C8C88 / 0x5C8C8F
        keep(b, low1, high1);                               // RE 0x5C8C94 / 0x5C8CA4 / 0x5C8CB2 / 0x5C8CBD
        keep(c, low0, high0);                               // RE 0x5C8CC6 / 0x5C8CD1 / 0x5C8CDB / 0x5C8CE2
        keep(d, low1, high1);                               // RE 0x5C8CE7 / 0x5C8CF2 / 0x5C8CFC / 0x5C8D06
    }

    /** The single-axis form kept for statExtent, which folds one measurement per element. It is NOT RE 0x5C8C50: it is a convenience for
     *  the accumulator at 0x526160, which uses one axis, and it is named apart so the two cannot be confused again. */
    void foldSingle(bool element_valid, double value, bool& seen, double& low, double& high) {
        if (!element_valid) {
            return;
        }
        if (!seen) {
            low = high = value;
            seen = true;
            return;
        }
        keep(value, low, high);
    }
};

'''

def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find(START)
    end = text.find(END)
    if start < 0 or end < 0 or end <= start:
        print("bounds not found: start=%d end=%d" % (start, end))
        return 1
    text = text[:start] + NEW + text[end:]
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote StatBox::fold from the whole body; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
