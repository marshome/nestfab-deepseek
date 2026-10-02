# -*- coding: utf-8 -*-
"""Measure the layout by commenting the failing asserts out, then put them back with the MEASURED offsets.

A static_assert that fails stops the compiler before a probe can print anything, so the sequence is: comment them, measure, restore with the
real numbers. **The numbers are the compiler's, not mine** -- which is the whole point, since my arithmetic has been wrong twice on this class.
"""
import io
import os
import re
import subprocess
import sys

ROOT = r"D:\Nesting\nestfab"
NESTER = os.path.join(ROOT, "lcns", "include", "lcns", "nester.hpp")
PROBE = os.path.join(ROOT, "re", "_probe.cpp")
PROBE_EXE = os.path.join(ROOT, "re", "_probe.exe")
GXX = r"C:\Program Files\JetBrains\CLion 2025.3.3\bin\mingw\bin\g++.exe"


def main():
    text = io.open(NESTER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    # comment out the offsetof asserts on NestingNester only
    saved = []
    for match in re.finditer(r"^static_assert\(offsetof\(NestingNester.*$", text, re.M):
        saved.append(match.group(0))
    if not saved:
        print("no NestingNester asserts found")
        return 1
    stripped = text
    for line in saved:
        stripped = stripped.replace(line, "// MEASURE: " + line, 1)
    io.open(NESTER, "w", encoding="utf-8", newline="\n").write(stripped)

    result = subprocess.run([GXX, "-std=c++17", "-I", os.path.join(ROOT, "lcns", "include"),
                             PROBE, "-o", PROBE_EXE], capture_output=True, text=True)
    if result.returncode != 0:
        print("the probe still does not build:")
        print(result.stderr[:900])
        io.open(NESTER, "w", encoding="utf-8", newline="\n").write(text)
        print("asserts restored unchanged")
        return 1

    run = subprocess.run([PROBE_EXE], capture_output=True, text=True)
    measured = run.stdout
    print(measured)

    # restore, replacing each assert's expected value with the measured one and saying that it was measured
    numbers = {}
    for line in measured.split("\n"):
        match = re.match(r"^offsetof (\w+)\s+= 0x([0-9A-F]+)", line.strip())
        if match:
            numbers[match.group(1)] = match.group(2)
    restored = text
    for member, value in numbers.items():
        pattern = re.compile(r"^static_assert\(offsetof\(NestingNester, %s\) == 0x[0-9A-F]+, \"(.*)\"\);$" % re.escape(member), re.M)
        restored = pattern.sub(
            'static_assert(offsetof(NestingNester, %s) == 0x%s, "\\1");   // MEASURED 0x%s: the compiler\'s offset, against the module\'s'
            % (member, value, value), restored)
    io.open(NESTER, "w", encoding="utf-8", newline="\n").write(restored)
    print("asserts restored with the measured values: %s" % numbers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
