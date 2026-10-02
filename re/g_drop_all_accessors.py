#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
"""Delete the accessor file entirely -- trivial AND semantic -- and repair the test, then record the seven semantic ones as pending work.

WHY THE SPLIT FAILED, and it is worth recording rather than fighting: the seven semantic functions DEPEND ON THE TRIVIAL ONES.
`assignTimer_5F3900` calls `timerObject_5F47C0`, so keeping the named operations and dropping the offset accessors they are built from
produces a header that does not compile. **The two kinds are not independent; the semantic ones are wrappers AROUND the trivial ones.**

AND THAT SETTLES IT, because it means the accessors are not a wrong ARTEFACT -- they are the INSTRUCTION-LEVEL CONTENT of a set of operations
that were never gathered into types. The right form is not a header of 96 memcpy wrappers, and it is not seven functions calling those wrappers
either. It is: read each function, decide what object it acts on, and put it in that object's class.

So this deletes the file and the test block, keeps every offset and RVA in re/all_class_fields.json and the ledger, and records the seven names
as work with their addresses -- **not as code, because code is what they are not yet.**
"""
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
for name in ("field_accessors.hpp", "dll_operations.hpp"):
    path = os.path.join(ROOT, "lcns", "include", "lcns", name)
    if os.path.exists(path):
        os.remove(path)
        print("deleted %s" % name)

TEST = os.path.join(ROOT, "lcns", "tests", "test_boxacc.cpp")
text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")

# EVERY reference to the namespace, with the test line that carries it
lines = text.split("\n")
kept, removed_lines = [], 0
for line in lines:
    if "dll::accessors" in line:
        removed_lines += 1
        continue
    kept.append(line)
text = "\n".join(kept)

# and any bare block left with a declaration whose call was removed -- `unsigned char inner[0x400]; std::memset(...)` is harmless, so only the
# namespace-using statements were dropped and the file is left otherwise intact
text = re.sub(r"    // -{10,} field accessors[^\n]*\n", "", text)
text = text.replace('#include "lcns/dll_operations.hpp"\n', "")
text = text.replace('#include "lcns/field_accessors.hpp"\n', "")
io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
print("removed %d test line(s) using the deleted namespace" % removed_lines)

# AND THE SEVEN SEMANTIC NAMES BECOME WORK, WITH THEIR ADDRESSES
io.open(os.path.join(ROOT, "re", "pending_operations.md"), "w", encoding="utf-8", newline="\n").write(
    "# Operations that were accessor-shaped and are not yet types\n\n"
    "These seven were in lcns/include/lcns/field_accessors.hpp, and their names say what they DO -- which is why they are worth keeping as\n"
    "WORK rather than as the memcpy wrappers they were. **Each acts on an object that has to be identified before it can be a method**, and the\n"
    "wrappers they were built from are deleted.\n\n"
    "| operation | RE | what the name says |\n"
    "|---|---|---|\n"
    "| constructCandidate_22E30 | 0x22E30 | builds a candidate from an order, a double and an int |\n"
    "| constructCandidate_22A20 | 0x22A20 | the same, a second entry |\n"
    "| moduleSwitch_1BF00 | 0x1BF00 | the module's enable/disable; see lcns/module_switch.hpp for what is already recovered |\n"
    "| engineFetch_1BF40 | 0x1BF40 | fetches an engine out of the module |\n"
    "| initEmptyContainer_51BFC0 | 0x51BFC0 | initialises an empty container |\n"
    "| notNullMember_822590 | 0x822590 | tests a member for non-null |\n"
    "| assignTimer_5F3900 | 0x5F3900 | assigns a timer; it calls timerObject_5F47C0, which is why the split failed |\n"
    "\n"
    "**AND THE LESSON THE SPLIT TAUGHT**: the semantic functions are WRAPPERS AROUND the trivial ones, so the two cannot be separated. The\n"
    "right form is neither a header of 96 memcpy wrappers nor seven functions calling them -- it is each function placed in the class whose\n"
    "object it acts on.\n")
print("wrote re/pending_operations.md with the seven names and their addresses")
