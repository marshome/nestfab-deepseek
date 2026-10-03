# -*- coding: utf-8 -*-
"""Prove the one-definition check fails on an UNRECORDED duplicate and passes when the share is too small to be one.

**A CHECK THAT HAS NEVER FAILED IS NOT KNOWN TO WORK, AND THIS ONE WAS WRONG THREE TIMES BEFORE IT WORKED** -- each version is in its own comments:

  1. grouping by (field count, field names) caught two LINEAR PROGRAM BACK-ENDS, which is not a duplication, and MISSED `Order` against
     `LaunchingOrderLayout` because their names differ;
  2. dividing by the SMALLER offset set reported 22 pairs, because the denominator measured the small struct rather than the relationship;
  3. adding a shared-field-name requirement then EXCLUDED the real duplication, whose two sides agree on only two names in 68.

So the proof plants a duplicate that is NOT recorded and requires a failure, then plants one whose share is too small and requires a pass.
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "g_one_definition.py")
PROBE = os.path.join(HERE, "..", "lcns", "include", "lcns", "_probe_duplicate.hpp")


def run():
    result = subprocess.run([sys.executable, CHECK], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.returncode, (result.stdout or "") + (result.stderr or "")


# **THE FIELDS ARE GIVEN THE LAYOUT'S OWN OFFSETS**, which is what makes them a duplicate of it rather than of anything else.
LAYOUT_OFFSETS = [0x000, 0x008, 0x00C, 0x010, 0x018, 0x01C, 0x020, 0x021, 0x022, 0x023, 0x028, 0x030, 0x038, 0x040,
                  0x044, 0x048, 0x050, 0x058, 0x05C, 0x060, 0x068, 0x06C, 0x070, 0x084, 0x085, 0x088]

PROBES = [
    ("A NEW duplicate over the layout's own offsets", True, LAYOUT_OFFSETS),
    ("A struct with too few shared offsets", False, [0x100, 0x108, 0x110, 0x118, 0x120, 0x128, 0x130, 0x138]),
]


def body_for(offsets):
    lines = ["#pragma once", "#include <cstdint>", "namespace probe {", "struct SecondLayout {"]
    for offset in offsets:
        lines.append("    std::uint64_t f%03X = 0;   // +0x%03X" % (offset, offset))
    lines.extend(["};", "}", ""])
    return "\n".join(lines)


def main():
    failures = []
    for label, should_fail, offsets in PROBES:
        io.open(PROBE, "w", encoding="utf-8", newline="\n").write(body_for(offsets))
        code, output = run()
        failed = code != 0
        named = next((line.strip() for line in output.split("\n") if "UNRECORDED" in line), "")
        print("%-52s expected %-6s got %-6s %s" % (label[:52], "FAIL" if should_fail else "PASS",
                                                   "FAIL" if failed else "PASS",
                                                   "correct" if failed == should_fail else "WRONG"))
        if named:
            print("      %s" % named[:88])
        if failed != should_fail:
            failures.append(label)
        os.remove(PROBE)

    code, _output = run()
    print("")
    print("and on the real tree it exits %d" % code)
    if failures:
        print("FAILING: the check is wrong about %s" % "; ".join(failures))
        return 1
    print("PASS: the check fails on an unrecorded duplicate and passes when the share is too small to be one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
