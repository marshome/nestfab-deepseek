# -*- coding: utf-8 -*-
"""Find the shape that produced the `Nester` failure: a `*gap*` constant standing in for a field the model does not declare.

**THE FAILURE WAS NOT A TYPO, IT WAS A METHOD, AND THIS IS THE CHECK THAT NAMES IT.** `lcns` declared `Nester` with no data while the module's base part is 0x18 bytes,
**so every field of every derived class was 0x10 too low** -- and a constant, `kNestingNesterBaseDataGap = 0x10`, plus five `member + gap == moduleOffset`
assertions, made that look measured. **An offset that needs arithmetic to reach is an offset the model does not have.**

**THE TWO HALVES ARE BOTH REQUIRED, WHICH IS WHY THIS IS NOT A REGEX OVER ONE FILE:**

  * **a non-zero `*gap*` constant**, and
  * **the `member + constant` arithmetic that consumes it**.

**AND A LEGITIMATE ONE EXISTS AND MUST NOT BE FLAGGED**: `kDefaultStubGap = 0x10` in layout.hpp is **the distance between two stub addresses** -- a fact about the
image's code layout, where `member + gap` is meaningless and does not appear. **A check that flags correct code gets switched off**, so the constant alone is not
enough and the arithmetic is required.

    python -u g_gap_compensation.py            -> exit 1 when such a pair exists
    python -u g_gap_compensation.py --list     -> what it looks at
"""
import argparse
import glob
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# a constexpr whose NAME says gap, holding a non-zero value
GAP_CONSTANT = re.compile(r"^\s*(?:inline\s+)?constexpr\s+[\w:<>\s]+\s+(\w*[Gg]ap\w*)\s*=\s*(0x[0-9A-Fa-f]+|\d+)\s*;", re.M)
# and `something + <that name>` in an assertion, which is the compensation being applied
GAP_ARITHMETIC = re.compile(r"[^\n]*\+[^\n]*\b(\w*[Gg]ap\w*)\b[^\n]*(?:==|!=)[^\n]*")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="print what was examined")
    args = parser.parse_args()

    headers = sorted(glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "*.hpp")))
    sources = sorted(glob.glob(os.path.join(ROOT, "lcns", "src", "*.cpp"))
                     + glob.glob(os.path.join(ROOT, "lcns", "tests", "*.cpp")))

    constants = {}
    for path in headers:
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in GAP_CONSTANT.finditer(text):
            value = int(match.group(2), 16) if match.group(2).startswith("0x") else int(match.group(2))
            if value:
                constants[match.group(1)] = (os.path.basename(path), value)

    consumed = {}
    for path in sources:
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in GAP_ARITHMETIC.finditer(text):
            consumed.setdefault(match.group(1), []).append((os.path.basename(path), match.group(0).strip()[:96]))

    if args.list:
        print("headers examined: %d, sources examined: %d" % (len(headers), len(sources)))
        print("non-zero `*gap*` constants: %d -- %s" % (len(constants), ", ".join(sorted(constants)) or "none"))
        print("of those, consumed as `member + constant == offset`: %d" % len(set(constants) & set(consumed)))

    offenders = sorted(set(constants) & set(consumed))
    if not offenders:
        print("OK: no `*gap*` constant is used as `member + constant == moduleOffset` -- every offset the model asserts is a modelled offset.")
        print("    (%d non-zero gap constant(s) exist and none is consumed that way, which is the legitimate case: they measure the image, not a missing field)"
              % len(constants))
        return 0

    print("**A `*gap*` CONSTANT COMPENSATES FOR A FIELD THE MODEL DOES NOT HAVE: %d**" % len(offenders))
    for name in offenders:
        where, value = constants[name]
        print("   %s = 0x%X   in %s" % (name, value, where))
        for source, line in consumed[name]:
            print("      %-22s %s" % (source, line))
    print("")
    print("**AN OFFSET THAT NEEDS ARITHMETIC TO REACH IS AN OFFSET THE MODEL DOES NOT HAVE.** Find the base constructor, establish the object register, and declare")
    print("the field -- then the gap is zero and the assertion says what the module says. `re/g_base_ctor.py` reads a constructor and lists its callers, and the")
    print("callers' own first offsets say how big the base part is.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
