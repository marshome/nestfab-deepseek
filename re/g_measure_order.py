# -*- coding: utf-8 -*-
"""Measure where Order's members ACTUALLY land, and compare with the offsets its comments claim.

**A COMMENT THAT SAYS `+0x44` IS A CLAIM ABOUT A LAYOUT**, and it is checkable in C++ against the declaration that carries it. If a struct's members do not
land where its own comments say, then the offsets were derived from individual STORES and the struct does not reproduce the module -- which is the same
distinction `re/row.hpp` settles for `Squeezer` by measuring rather than by declaring.

This prints both columns so the difference is visible, and asserts nothing: the answer decides what the reconciliation has to do.
"""
import io
import os
import re
import subprocess
import sys
import tempfile

ROOT = r"D:\Nesting\nestfab"
GXX = r"C:\Program Files\JetBrains\CLion 2025.3.3\bin\mingw\bin\g++.exe"


def main():
    model = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "model.hpp"), encoding="utf-8").read()
    match = re.search(r"struct Order\s*\{(?P<body>.*?)\n\};", model, re.S)
    if not match:
        print("REFUSING: Order is not found")
        return 2
    body = match.group("body")
    FIELD = re.compile(r"^\s+([\w:<>,\s\*&]+?)\s+\b(\w+)\s*(\[[^\]]*\])?\s*(?:=[^;]*)?;\s*//[^\n]*?\+0x([0-9A-Fa-f]+)", re.M)
    fields = [(m.group(1).strip() + (" " + m.group(3) if m.group(3) else ""), m.group(2), int(m.group(4), 16))
              for m in FIELD.finditer(body)]
    print("Order declares %d offset-commented fields" % len(fields))

    # build a program that prints offsetof for each, using a declared instance rather than offsetof on a polymorphic type
    lines = ['#include "lcns/model.hpp"', "#include <cstdio>", "int main() {",
             "    lcns::Order o;", "    const unsigned char* base = reinterpret_cast<const unsigned char*>(&o);"]
    for ftype, name, offset in fields:
        lines.append('    std::printf("%%s\\t0x%%03X\\t0x%%03X\\n", "%s", %d, static_cast<unsigned>(reinterpret_cast<const unsigned char*>(&o.%s) - base));'
                     % (name, offset, name))
    lines.append("    return 0;")
    lines.append("}")
    source = "\n".join(lines)

    with tempfile.TemporaryDirectory() as work:
        path = os.path.join(work, "probe.cpp")
        io.open(path, "w", encoding="utf-8", newline="\n").write(source)
        result = subprocess.run([GXX, "-std=c++17", "-I", os.path.join(ROOT, "lcns", "include"), "-o",
                                 os.path.join(work, "probe.exe"), path],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            print("REFUSING: the probe did not compile")
            print((result.stderr or "")[:1500])
            return 1
        run = subprocess.run([os.path.join(work, "probe.exe")], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        print("REFUSING: the probe did not run")
        return 1

    mismatched = []
    for line in (run.stdout or "").split("\n"):
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        name, claimed, actual = parts[0], int(parts[1], 16), int(parts[2], 16)
        if claimed != actual:
            mismatched.append((name, claimed, actual))
    print("")
    print("%-40s %-10s %s" % ("field", "comment", "measured"))
    for line in (run.stdout or "").split("\n")[:12]:
        parts = line.split("\t")
        if len(parts) == 3:
            print("%-40s %-10s %s" % (parts[0], parts[1], parts[2]))
    print("")
    print("fields whose comment and measurement DISAGREE: %d of %d" % (len(mismatched), len(fields)))
    for name, claimed, actual in mismatched[:16]:
        print("   %-40s comment 0x%03X  measured 0x%03X" % (name, claimed, actual))
    return 0


if __name__ == "__main__":
    sys.exit(main())
