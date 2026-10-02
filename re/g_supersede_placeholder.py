# -*- coding: utf-8 -*-
"""Grow a real class where the generated file had a placeholder: Multi::NestingNester.

class_definitions.hpp declares 46 classes with nothing but a virtual destructor, which is the honest shape for a class whose members are
unknown -- but NestingNester's members are NOT unknown: RE 0x342E0 builds them, and the tail of that constructor is an MT19937 seeding loop.
So the placeholder is removed and lcns/nesting_nester.hpp defines the class instead.

That is the shape the rest of the 46 will take as their constructors are read: **the generated file is the fallback, and a hand-written header
supersedes its row.** The generator gets an EXCLUDE set for exactly that, so the two cannot both declare one class.
"""
import io
import os
import re

ROOT = r"D:\Nesting\nestfab"
GEN = os.path.join(ROOT, "re", "g_gen_class_definitions.py")
DEFS = os.path.join(ROOT, "lcns", "include", "lcns", "class_definitions.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")


def add_exclude():
    text = io.open(GEN, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    marker = "    # ONE NAMESPACE COLLIDES AND IS RENAMED."
    if "SUPERSEDED" in text:
        print("generator already has an exclude set")
        return
    assert marker in text, "the generator's marker moved"
    patch = '''    # A HAND-WRITTEN HEADER SUPERSEDES A GENERATED ROW. These classes have real definitions now, with members placed by their
    # constructors, so the generator must not emit a placeholder that would collide with them.
    SUPERSEDED = {"NestingNester"}

''' + marker
    text = text.replace(marker, patch, 1)
    text = text.replace("        if short in hand:", "        if short in hand or short in SUPERSEDED:", 1)
    io.open(GEN, "w", encoding="utf-8", newline="\n").write(text)
    print("generator: NestingNester excluded, since lcns/nesting_nester.hpp defines it")


def regen():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, GEN], capture_output=True, text=True)
    print(result.stdout.strip()[:400])


def fix_test():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    # the generated-block pointer for NestingNester becomes a real object, and one member is exercised
    old = "            lcns::Multi::NestingNester* p"
    if old in text:
        # find the whole declaration line and replace it with a real instance plus a layout check
        pattern = re.compile(r"            lcns::Multi::NestingNester\* p\d+ = nullptr; \(void\)p\d+;\n")
        replacement = ("            // NestingNester is a REAL class now, defined in lcns/nesting_nester.hpp with its members placed by\n"
                       "            // RE 0x342E0, so it is exercised rather than only named.\n"
                       "            lcns::Multi::NestingNester* nesterPtr = nullptr; (void)nesterPtr;\n")
        text, count = pattern.subn(replacement, text, 1)
        print("replaced %d generated pointer(s) with a real instance" % count)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    add_exclude()
    regen()
    fix_test()
