# -*- coding: utf-8 -*-
"""Prove the offset-compensation check fails on the shape it exists for, and passes the legitimate one.

**A CHECK THAT HAS NEVER FAILED IS NOT KNOWN TO WORK**, and this one exists because `lcns` declared `Nester` with no data while the module's base part is 0x18 bytes
-- **a constant and five `member + gap == offset` assertions made an unmodelled field look measured.** So both halves are planted:

  * **a `*gap*` constant consumed by `member + constant == offset`** -- the defect, which must fail
  * **a `*gap*` constant measuring the image and not consumed that way** -- which must pass, because `kDefaultStubGap` is exactly that and **a check that flags
    correct code gets switched off.**
"""
import io
import os
import subprocess
import sys

ROOT = r"D:\Nesting\nestfab"
PLANT = os.path.join(ROOT, "lcns", "include", "lcns", "_probe_gap.hpp")
PLANT_SOURCE = os.path.join(ROOT, "lcns", "tests", "_probe_gap.cpp")
CHECK = os.path.join(ROOT, "re", "g_gap_compensation.py")


def run():
    result = subprocess.run([sys.executable, CHECK], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.returncode, (result.stdout or "")


def main():
    failures = []

    # 1. a gap constant MEASURING THE IMAGE, not consumed as `member + gap` -- must pass
    io.open(PLANT, "w", encoding="utf-8", newline="\n").write(
        "#pragma once\nnamespace lcns {\n"
        "inline constexpr unsigned kProbeStubA = 0x7C2460;\n"
        "inline constexpr unsigned kProbeStubGap = 0x10;   // the two stubs are one object apart\n"
        "}\n")
    code, out = run()
    print("planted %-58s -> exit %d  %s" % ("a gap constant that measures the image", code, "PASS" if code == 0 else "FLAGGED"))
    if code != 0:
        failures.append("the legitimate form was flagged")
    os.remove(PLANT)

    # 2. the same constant CONSUMED by `member + gap == offset` -- must fail and name it
    io.open(PLANT, "w", encoding="utf-8", newline="\n").write(
        "#pragma once\nnamespace lcns {\n"
        "inline constexpr unsigned kProbeBaseDataGap = 0x10;\n"
        "}\n")
    io.open(PLANT_SOURCE, "w", encoding="utf-8", newline="\n").write(
        "// a probe\nvoid probe() {\n    const int atSeedP = 0x08;\n    (void)(atSeedP + lcns::kProbeBaseDataGap == 0x18);\n}\n")
    code, out = run()
    named = "kProbeBaseDataGap" in out
    print("planted %-58s -> exit %d  named=%s" % ("a gap constant consumed as `member + gap`", code, named))
    if code == 0 or not named:
        failures.append("the defect was not caught and named")
    os.remove(PLANT)
    os.remove(PLANT_SOURCE)

    # 3. and the tree itself must pass
    code, out = run()
    print("planted %-58s -> exit %d" % ("(nothing: the tree as it stands)", code))
    if code != 0:
        failures.append("the tree itself does not pass the check")

    print("")
    if failures:
        print("FAILING: %s -- so a PASS from this check means nothing." % "; ".join(failures))
        return 1
    print("PASS: it flags the compensation, names the constant, and leaves the legitimate form alone.")
    print("")
    print("WHAT IT CANNOT CATCH, stated rather than assumed:")
    print("   * **a WRONG offset with no gap constant at all** -- a model that is simply wrong by 8 bytes somewhere and asserts that number everywhere. The check")
    print("     reads constants and arithmetic, so it sees a compensation and not a mistake.")
    print("   * **a base whose fields are declared but WRONG** -- it would pass here and fail in the layout test, which is the check that caught this round's")
    print("     first attempt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
