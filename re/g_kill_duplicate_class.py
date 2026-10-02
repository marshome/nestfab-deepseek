# -*- coding: utf-8 -*-
"""Delete the two duplicate descriptions of NestingNester I created, and add the constructor the class now declares.

WHAT WENT WRONG, in the human's terms: `class NestingNester : public Nester` was already in nester.hpp with name(), estimate() and run() -- and
nester.cpp already implements estimate and run. **I then wrote a SECOND description of the same class in two new files**, which is three
descriptions of one class:

    nester.hpp                    the real class, with behaviour
    nesting_nester_layout.hpp     NestingNesterLayout -- my duplicate, no behaviour
    class_layouts.hpp             NestingNesterLayout again, generated from the fields scan

**A class that already exists does not get a second declaration.** The members the constructor places are ADDED to the class that exists, and
the duplicates are deleted. That is the rule, and the audit script in re/g_audit_cpp.py is what finds the next violation.
"""
import io
import os
import sys

ROOT = r"D:\Nesting\nestfab"
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")
DELETE = ["nesting_nester_layout.hpp", "class_layouts.hpp"]
SRC = os.path.join(ROOT, "lcns", "src", "nester.cpp")


def add_constructor():
    text = io.open(SRC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "NestingNester::NestingNester" in text:
        print("the constructor is already defined")
        return
    body = '''
// RE 0x342E0's first two stores, which is the part of the constructor the class itself can perform. The rest of 0x342E0 seeds a 624 word
// Mersenne Twister and computes a ratio from two measurements, and those belong to the algorithm rather than to the object's construction --
// so this installs the two pointers and leaves the seeding to `seed()`, which is where the loop's content is read.
NestingNester::NestingNester(const SeedPair& seeds) : seedP(seeds.first), seedQ(seeds.second) {}

'''
    marker = "double NestingNester::estimate(const SolveContext& ctx) const {"
    if marker not in text:
        print("REFUSING: the estimate definition is not where it was")
        return
    text = text.replace(marker, body.lstrip("\n") + marker, 1)
    io.open(SRC, "w", encoding="utf-8", newline="\n").write(text)
    print("added NestingNester's constructor to nester.cpp")


def remove_from_test():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    # drop the layout-class test block, which tested my duplicate
    start = text.find("    // ---------------------------------------------------------------- Multi::NestingNester as a CLASS")
    end = text.find("    // ---------------------------------------------------------------- records as STRUCTS")
    if start >= 0 and end > start:
        replacement = ("    // ---------------------------------------------------------------- Multi::NestingNester's members\n"
                       "    //\n"
                       "    // A `NestingNesterLayout` class stood here. **The class already existed** -- `class NestingNester : public\n"
                       "    // Nester` in nester.hpp, with name(), estimate() and run() implemented in nester.cpp -- so the members its\n"
                       "    // constructor places were ADDED to it and the duplicate was deleted. The assertions below are the offsets.\n"
                       "    {\n"
                       "        using lcns::NestingNester;\n"
                       "        CHECK(offsetof(NestingNester, seedP) == 0x18u);      // RE 0x34312\n"
                       "        CHECK(offsetof(NestingNester, seedQ) == 0x20u);      // RE 0x3430E\n"
                       "        CHECK(offsetof(NestingNester, seed) == 0x28u);       // RE 0x34341\n"
                       "        CHECK(offsetof(NestingNester, ratio) == 0x30u);      // RE 0x343E3\n"
                       "        CHECK(offsetof(NestingNester, twister) == 0x38u);    // RE 0x34354\n"
                       "        CHECK(lcns::Mt19937::kStateSize == 624u);            // RE 0x3435C\n"
                       "        CHECK(lcns::Mt19937::kSeedMultiplier == 0x6C078965u); // RE 0x3434B\n"
                       "        CHECK(offsetof(lcns::Mt19937, index) == 624u * 4u);\n"
                       "        CHECK(offsetof(lcns::SeedPair, second) == 0x08u);    // RE 0x34301\n"
                       "\n"
                       "        // AN INSTANCE IS BUILT THROUGH THE CONSTRUCTOR THE MODULE HAS, and its members are the module's\n"
                       "        lcns::SeedPair seeds;\n"
                       "        seeds.first = reinterpret_cast<void*>(0x1111);\n"
                       "        seeds.second = reinterpret_cast<void*>(0x2222);\n"
                       "        NestingNester nester(seeds);\n"
                       "        CHECK(nester.seedP == seeds.first);\n"
                       "        CHECK(nester.seedQ == seeds.second);\n"
                       "        CHECK(nester.twister.index == lcns::Mt19937::kStateSize);\n"
                       "        CHECK(nester.name() != nullptr);\n"
                       "    }\n\n")
        text = text[:start] + replacement + text[end:]
        print("replaced the duplicate-class test with member assertions")
    for include in ('#include "lcns/nesting_nester_layout.hpp"\n', '#include "lcns/class_layouts.hpp"\n'):
        if include in text:
            text = text.replace(include, "", 1)
            print("removed %s" % include.strip())
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    add_constructor()
    remove_from_test()
    for name in DELETE:
        path = os.path.join(ROOT, "lcns", "include", "lcns", name)
        if os.path.exists(path):
            os.remove(path)
            print("deleted %s" % name)
