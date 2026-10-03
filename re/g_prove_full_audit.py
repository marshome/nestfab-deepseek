# -*- coding: utf-8 -*-
"""Prove the full audit fails on each fabricated shape, and say what it CANNOT catch.

**A CHECK THAT HAS NEVER FAILED IS NOT KNOWN TO WORK**, and this one passes on a repository where the human found four separate instances of the
defect -- because all four were deleted first. So each shape is planted in turn and the audit must fail and name it.

AND THE LIMITS ARE STATED HERE RATHER THAN LEFT TO BE DISCOVERED: the audit catches SHAPES, not WRONG CLAIMS. A member called `ratio_` whose
instruction does not exist looks exactly like a member whose instruction does, because there is no instruction to look at.
"""
import io
import os
import subprocess
import sys

ROOT = r"D:\Nesting\nestfab"
PLANT = os.path.join(ROOT, "lcns", "include", "lcns", "_probe_fabricated.hpp")
AUDIT = os.path.join(ROOT, "re", "g_full_cpp_audit.py")

CASES = [
    ("a member named after its offset",
     "struct Probe {\n    void* at_0020 = {};\n};\n"),
    ("a member whose comment cites a stack store",
     "struct Probe {\n    void* slot = {}; // +0x20, RE 0x50CFCA: mov qword ptr [rsp + 0x20], rax\n};\n"),
    # **AND THE ADDRESS-ONLY FORM IS PROVED SEPARATELY, BECAUSE IT IS A REPORT AND NOT A GATE.** Every real annotation says `RE 0xD062` and leaves the instruction in
    # the image; **the first version of the stack check matched only literal instruction text, so it reported 0 while `launching_order.hpp`'s `unnamed028` cited a
    # stack store for its width** -- and the plant above passed, because the plant wrote the instruction out. **A proof whose fixture is a shape the repository does
    # not produce proves nothing about it**, so this shape is planted and the REPORT is required to name it.
    ("an unplaced byte region standing in for a type",
     "struct Probe {\n    std::byte unplaced_0008[0x18]{};\n};\n"),
    ("a placeholder class",
     "class Probe {\npublic:\n    virtual ~Probe() = default;\n};\n"),
]


def main():
    failures = []
    for label, body in CASES:
        io.open(PLANT, "w", encoding="utf-8", newline="\n").write("#pragma once\n#include <cstddef>\nnamespace lcns {\n" + body + "}\n")
        result = subprocess.run([sys.executable, AUDIT], capture_output=True, text=True, encoding="utf-8", errors="replace")
        named = [line.strip() for line in (result.stdout or "").split("\n") if "_probe_fabricated.hpp" in line]
        caught = result.returncode != 0 and bool(named)
        print("planted %-52s -> exit %d  %s" % (label, result.returncode, named[0][:60] if named else "NOT NAMED"))
        if not caught:
            failures.append(label)
        os.remove(PLANT)

    # **AND THE ADDRESS-ONLY FORM, WHICH IS A REPORT AND NOT A GATE.** Every real annotation says `RE 0xD062` and leaves the instruction in the image; **the first
    # version of the stack check matched only literal instruction text, so it reported 0 while `launching_order.hpp`'s `unnamed028` cited a stack store for its
    # width** -- and the plant above passed, because that plant writes the instruction out. **A proof whose fixture is a shape the repository does not produce proves
    # nothing about the repository.** So this one plants the address-only form and requires the REPORT to name it while the exit code stays 0.
    io.open(PLANT, "w", encoding="utf-8", newline="\n").write(
        "#pragma once\n#include <cstddef>\nnamespace lcns {\nstruct Probe {\n"
        "    std::int64_t slot = 0;   // +0x028  RE 0xD062: the width was read off a stack store\n};\n}\n")
    result = subprocess.run([sys.executable, AUDIT], capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = result.stdout or ""
    reported = "_probe_fabricated.hpp" in output and "STACK-STORE REPORTS" in output
    gated = result.returncode != 0
    print("planted %-52s -> exit %d  reported=%s gated=%s"
          % ("a member citing an ADDRESS that writes the stack", result.returncode, reported, gated))
    if not reported or gated:
        failures.append("the address-only stack form (reported=%s, gated=%s)" % (reported, gated))
    os.remove(PLANT)

    print("")
    if failures:
        print("FAILING: the audit did not catch %s, so its PASS means nothing." % "; ".join(failures))
        return 1
    print("PASS: the audit fails on all %d shapes, and names the file." % len(CASES))
    print("")
    print("WHAT IT CANNOT CATCH, stated so the gap is known rather than assumed:")
    print("   * a member whose NAME is wrong but whose position is right -- `ratio_` where the module has two booleans. There is no")
    print("     instruction to compare against, because the member was never placed by one.")
    print("   * a member at a plausible offset that NO instruction writes. The audit sees a member and an offset comment.")
    print("   * a class that exists twice under different names.")
    print("Those need reading, which is what the human has been doing, and each one found so far is recorded in re/ledger.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
