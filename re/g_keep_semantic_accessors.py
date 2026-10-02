#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Keep SEVEN named operations, delete the rest, and let the compiler name the test references to remove.

    KEPT, because the name says what the function DOES:
        constructCandidate_22E30, constructCandidate_22A20   builds a candidate from an order and a double
        moduleSwitch_1BF00                                   the module's enable/disable
        engineFetch_1BF40                                    fetches an engine out of the module
        initEmptyContainer_51BFC0                            initialises an empty container
        notNullMember_822590                                 tests a member for non-null
        assignTimer_5F3900                                   assigns a timer
        clear2_8774E0                                        a clear

    DELETED, because the name is its own offset and its own RVA -- `getDword00_52F920`, `setDouble58_4F9C20`, `getPtr00_4FC1D0`:
    **a calling convention rather than a program.** An accessor at +0x60 of `the object` is a function about an object that has not been
    identified, and 87 of them were that.
"""
import io
import os
import re
import subprocess
import sys

ROOT = r"D:\Nesting\nestfab"
KEEP = os.path.join(ROOT, "lcns", "include", "lcns", "dll_operations.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")

SEMANTIC = {"constructCandidate_22E30", "constructCandidate_22A20", "moduleSwitch_1BF00", "engineFetch_1BF40",
            "initEmptyContainer_51BFC0", "notNullMember_822590", "assignTimer_5F3900", "clear2_8774E0"}


def rewrite_header():
    text = io.open(KEEP, encoding="utf-8", errors="replace").read()
    blocks = re.split(r"\n(?=/\*\* RE 0x)", text)
    kept, dropped = [], []
    for block in blocks:
        found = re.search(r"inline [\w:<> ]+ (\w+)\(", block)
        if not found:
            continue
        if found.group(1) in SEMANTIC:
            kept.append(block.rstrip())
        else:
            dropped.append(found.group(1))
    print("kept %d, dropped %d" % (len(kept), len(dropped)))
    head = text[:text.find("/** RE 0x")] if "/** RE 0x" in text else text
    io.open(KEEP, "w", encoding="utf-8", newline="\n").write(
        head + "\n".join(kept) + "\n\n}  // namespace accessors\n}  // namespace dll\n}  // namespace lcns\n")
    return dropped


def main():
    dropped = rewrite_header()

    # REMOVE EVERY TEST LINE THAT REFERENCES A DROPPED FUNCTION, and any block left empty by it
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = text.split("\n")
    kept_lines = []
    removed = 0
    for line in lines:
        if any(("accessors::" + name) in line for name in dropped):
            removed += 1
            continue
        kept_lines.append(line)
    text = "\n".join(kept_lines)
    # and the comment headings of the batches those lines belonged to
    text = re.sub(r"    // -{10,} field accessors[^\n]*\n", "", text)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("removed %d test line(s) referencing a dropped accessor" % removed)
    print("test_boxacc.cpp: %d lines" % text.count("\n"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
