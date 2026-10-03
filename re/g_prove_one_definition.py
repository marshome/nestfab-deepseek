# -*- coding: utf-8 -*-
"""Prove the one-definition check fails on a NEW duplicate and passes when it is recorded.

**A CHECK THAT HAS NEVER FAILED IS NOT KNOWN TO WORK, AND THIS ONE WAS WRONG THREE TIMES BEFORE IT WORKED** -- each version is in its own comments:

  1. grouping by (field count, field names) caught two LINEAR PROGRAM BACK-ENDS, which is not a duplication at all, and missed `Order` against
     `LaunchingOrderLayout` because their names differ;
  2. dividing by the SMALLER offset set reported 22 pairs, because the denominator measured the small struct rather than the relationship;
  3. adding a shared-field-name requirement then EXCLUDED the real duplication, whose two sides agree on 2 names in 45 -- one naming a field by the
     export that sets it and the other by its offset.

So the proof plants a duplicate that is NOT in the recorded lists and requires a failure, then plants one that IS recorded and requires a pass.
"""
import io
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "g_one_definition.py")
PROBE = os.path.join(HERE, "..", "lcns", "include", "lcns", "_probe_duplicate.hpp")


def run():
    result = subprocess.run([sys.executable, CHECK], capture_output=True, text=True, encoding="utf-8")
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def main():
    failures = []
    probes = [
        ("A NEW duplicate of LaunchingOrderLayout, unrecorded", """#pragma once
#include <cstdint>
namespace probe {
struct SecondOrderLayout {
    double a;   // +0x010
    double b;   // +0x018
    double c;   // +0x020
    double d;   // +0x028
    double e;   // +0x030
    double f;   // +0x038
    double g;   // +0x040
    double h;   // +0x048
    double i;   // +0x050
    double j;   // +0x058
    double k;   // +0x060
    double l;   // +0x068
    double m;   // +0x070
    double n;   // +0x078
    double o;   // +0x080
    double p;   // +0x088
    double q;   // +0x090
    double r;   // +0x098
    double s;   // +0x0A0
    double t;   // +0x0A8
    double u;   // +0x0B0
    double v;   // +0x0B8
};
}
""", True),
        ("A struct with too few shared offsets", """#pragma once
#include <cstdint>
namespace probe {
struct Tiny {
    double a;   // +0x010
    double b;   // +0x018
    double c;   // +0x020
    double d;   // +0x028
    double e;   // +0x030
    double f;   // +0x038
    double g;   // +0x040
    double h;   // +0x048
    double i;   // +0x050
    double j;   // +0x058
};
}
""", False),
    ]

    for label, body, should_fail in probes:
        io.open(PROBE, "w", encoding="utf-8", newline="\n").write(body)
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

    code, _ = run()
    print("")
    print("and on the real tree it exits %d" % code)
    if failures:
        print("FAILING: the check is wrong about %s" % "; ".join(failures))
        return 1
    print("PASS: the check fails on an unrecorded duplicate and passes when the share is too small to be one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
