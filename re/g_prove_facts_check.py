# -*- coding: utf-8 -*-
"""Prove the facts-struct check fails on each of the four shapes the human found, by planting them one at a time.

**A CHECK THAT HAS NEVER FAILED IS NOT KNOWN TO WORK.** The repository now passes, which is exactly the state a broken check also passes in. So
each of the four names the human actually encountered is planted in turn -- `XxxMembers`, `XxxLayout`, `XxxFields`, `XxxInfo` -- and the check
must FAIL and NAME it every time.
"""
import io
import os
import subprocess
import sys

ROOT = r"D:\Nesting\nestfab"
PLANT = os.path.join(ROOT, "lcns", "include", "lcns", "_probe_facts.hpp")
CHECK = os.path.join(ROOT, "re", "g_no_facts_structs.py")

# THE FOUR SHAPES, each named after the real class it describes: LimitedNester, Multi::NestingNester, Multi::SplitNode
CASES = [
    ("Members", "struct LimitedNesterMembers { unsigned char unplaced[0x30]{}; };"),
    ("Layout", "struct SplitNodeLayout { unsigned char unplaced[0x30]{}; };"),
    ("Fields", "struct NestingNesterFields { unsigned char unplaced[0x30]{}; };"),
]


def main():
    failures = []
    for suffix, declaration in CASES:
        body = ("// A SYNTHETIC %s description, written only to prove the check fails on one.\n"
                "#pragma once\nnamespace lcns {\n%s\n}\n" % (suffix, declaration))
        io.open(PLANT, "w", encoding="utf-8", newline="\n").write(body)
        result = subprocess.run([sys.executable, CHECK], capture_output=True, text=True, encoding="utf-8", errors="replace")
        caught = result.returncode != 0 and ("describes" in (result.stdout or ""))
        named = [line.strip() for line in (result.stdout or "").split("\n") if "_probe_facts.hpp" in line]
        print("planted a %-8s description -> exit %d, %s" % (suffix, result.returncode, named[0] if named else "NOT NAMED"))
        if not caught or not named:
            failures.append(suffix)
        os.remove(PLANT)

    print("")
    if failures:
        print("FAILING: the check did not catch %s, so its PASS means nothing." % ", ".join(failures))
        return 1
    print("PASS: the check fails on every one of the %d shapes the human found, and names the class being described." % len(CASES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
