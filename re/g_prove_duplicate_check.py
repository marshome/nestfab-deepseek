# -*- coding: utf-8 -*-
"""Prove the duplicate-struct check FAILS on a duplicate, by planting one and removing it again.

**A CHECK THAT HAS NEVER FAILED IS NOT KNOWN TO WORK.** The check passes on the repository as it stands, which is exactly the state in which a
broken check also passes. So a synthetic `LimitedNesterMembers` is written beside the real thing, the check is run expecting failure, and the
file is deleted.
"""
import io
import os
import subprocess
import sys

ROOT = r"D:\Nesting\nestfab"
PLANT = os.path.join(ROOT, "lcns", "include", "lcns", "_probe_duplicate.hpp")
CHECK = os.path.join(ROOT, "re", "g_no_duplicate_structs.py")

SYNTHETIC = """// A SYNTHETIC duplicate, written only to prove the check fails on one. Deleted immediately after.
#pragma once
namespace lcns {
struct LimitedNesterMembers {
    unsigned char unplaced_0008[0x30]{};
};
}
"""


def main():
    io.open(PLANT, "w", encoding="utf-8", newline="\n").write(SYNTHETIC)
    result = subprocess.run([sys.executable, CHECK], capture_output=True, text=True, encoding="utf-8")
    print("with a synthetic duplicate planted, the check reports:")
    for line in (result.stdout or "").strip().split("\n"):
        print("   %s" % line)
    print("   exit code: %d" % result.returncode)
    os.remove(PLANT)
    print("")
    if result.returncode != 0 and "LimitedNester" in (result.stdout or ""):
        print("PASS: the check FAILS on a second description of an existing class, and names it.")
        return 0
    print("FAILING: the check did not notice the planted duplicate, so its PASS means nothing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
