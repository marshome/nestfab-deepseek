# -*- coding: utf-8 -*-
"""Prove the address-named-function check fails on the real shape and passes on the two legitimate ones.

**A CHECK THAT HAS NEVER FAILED IS NOT KNOWN TO WORK**, and this one has now been wrong THREE times -- flagging `setAutomaticStop_0E010` (a name
that does say what it does), the embedded shims, and three explanatory comments. Each correction is in the check's own comments. So the proof is
a program: plant the `field_accessors.hpp` shape, require failure, and require a PASS on the two legitimate forms.
"""
import io
import os
import subprocess
import sys

ROOT = r"D:\Nesting\nestfab"
PLANT = os.path.join(ROOT, "lcns", "include", "lcns", "_probe_named.hpp")
CHECK = os.path.join(ROOT, "re", "g_no_address_named_functions.py")

# (label, body, should it fail?)
CASES = [
    ("the accessor shape: <verb><width><offset>_<rva>",
     "inline std::uint32_t getDword00_52F920(const void* object) { return 0; }\n", True),
    ("a semantic name that keeps the RVA as evidence",
     "inline void setAutomaticStop_0E010(void* object, int value) { (void)object; (void)value; }\n", False),
    ("an embedded shim, whose only identifier is its address",
     "const unsigned char* sub_0AFE0(void);\n", False),
    ("a COMMENT naming an anonymous export",
     "// sub_16CF0 (210/211): the same getter as GetPartUserString, without the logger call.\n", False),
]


def main():
    failures = []
    for label, body, should_fail in CASES:
        io.open(PLANT, "w", encoding="utf-8", newline="\n").write(
            "#pragma once\n#include <cstdint>\nnamespace lcns {\n" + body + "}\n")
        result = subprocess.run([sys.executable, CHECK], capture_output=True, text=True, encoding="utf-8", errors="replace")
        failed = result.returncode != 0
        named = [line.strip() for line in (result.stdout or "").split("\n") if "_probe_named.hpp" in line]
        verdict = "correct" if failed == should_fail else "WRONG"
        if failed != should_fail:
            failures.append(label)
        print("%-44s expected %-9s got %-9s %s" % (label[:44], "FAIL" if should_fail else "PASS",
                                                   "FAIL" if failed else "PASS", verdict))
        if failed and named:
            print("      %s" % named[0][:80])
        os.remove(PLANT)
    print("")
    if failures:
        print("FAILING: the check is wrong about %s." % "; ".join(failures))
        return 1
    print("PASS: the check fails on the accessor shape and passes on both legitimate forms.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
