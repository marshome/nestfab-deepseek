# -*- coding: utf-8 -*-
"""Remove the unused helper the wrappers do not need, and say why it was unused.

The build rejected the helper as `-Wunused-function`, and the warning was right for a better reason than tidiness: the two wrappers
TAIL CALL 0x132E0 and never use the double it returns, so the scaled extent is 0x132E0's internal computation rather than
something the exports hand back. A helper defined and not called was the compiler noticing that the implementation described more
than the export does.
"""
import io

PATH = r"D:\Nesting\nestfab\lcns\src\exports_impl.cpp"

HELPER = '''namespace {

/** RE 0x132E0's rule, given a box the caller supplies: invalid scales nothing, otherwise the larger extent times the constant.
 *
 * The box is the caller's because the real routine fills it by walking a container, and the walk is RE 0x5CD5C0 -- reading it here
 * would mean reproducing a container traversal whose element type is not yet declared. The RULE is what the export contributes.
 */
double variantScaledExtent(const lcns::StatBox& box, bool valid) {
    const double extentA = box.high0 - box.low0;      // RE 0x13335
    const double extentB = box.high1 - box.low1;      // RE 0x1333B
    return lcns::variantScale(valid, extentA, extentB, lcns::kVariantScale);
}

}  // namespace

'''

NOTE = '''// WHY THERE IS NO SCALED VALUE HERE, and the build said so first: the two wrappers TAIL CALL 0x132E0 and never use the double it
// returns, so the scaling is 0x132E0's internal computation. Writing a helper that computes it and is never called described more
// than the export does, and `-Wunused-function` was the compiler pointing that out. The rule lives in lcns/include/lcns/variant.hpp
// where it is tested, and the wrappers stay as thin as the module's are.

'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if HELPER not in text:
        print("the helper is not present verbatim; nothing changed")
        return 1
    text = text.replace(HELPER, NOTE, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("removed the unused helper and recorded why")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
