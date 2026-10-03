# -*- coding: utf-8 -*-
"""Rename the `Solution` handle the way `Order` was renamed, because it is used ONLY as a parameter.

**THE MEASUREMENT SAYS WHY THIS ONE IS SAFE**: `re/g_handle_usage.py` finds `Solution` in wrapper PARAMETER lists and in no return type -- so the C ABI does not
change (both `SolutionHandle` and `Solution_t*` are `Solution*`) and no stub's `return 0` has to become something else. **The other six collide as RETURN types too**,
and there a rename would change what 121 functions return, **which is a recovered behaviour and not a rename.**

**AND THE COMMENTS AND STRINGS ARE LIFTED OUT FIRST.** The generated files are mostly prose, and a `\\bSolution\\b` substitution rewrites the sentences that
explain the rename -- which is what happened to `Order`'s explanation before the guard was added.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
FILES = [
    (os.path.join(ROOT, "lcns", "include", "lcns", "api.hpp"), True),
    (os.path.join(ROOT, "lcns", "src", "api_exports.cpp"), False),
    (os.path.join(ROOT, "lcns", "include", "lcns", "detail", "api_typed.inc"), False),
]


def main(apply):
    for path, is_header in FILES:
        text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        if is_header:
            old = "LCNS_OPAQUE(Solution);     // SolveResult"
            new = ("// **`Solution` IS THE REAL CLASS IN lcns/model.hpp, SO THE HANDLE IS NAMED `SolutionHandle`** -- the same rename `Order` needed, and for the same\n"
                   "// reason: `using Solution = Solution_t*` beside `struct Solution` is two declarations of one name.\n"
                   "struct Solution_t;\n"
                   "using SolutionHandle = Solution_t*;   // SolveResult")
            if old not in text:
                print("   api.hpp: the anchor is not there (already renamed?)")
                continue
            text = text.replace(old, new, 1)
            io.open(path, "w", encoding="utf-8", newline="\n").write(text)
            print("   api.hpp: the handle is now SolutionHandle")
            continue

        literals = []

        def stash(match):
            literals.append(match.group(0))
            return "\x00%d\x00" % (len(literals) - 1)

        text = re.sub(r'//[^\n]*|/\*.*?\*/|"(?:[^"\\]|\\.)*"', stash, text, flags=re.S)
        before = len(re.findall(r"\bSolution\b", text))
        text = re.sub(r"\bSolution\b(?!\w)", "SolutionHandle", text)
        text = re.sub(r"\x00(\d+)\x00", lambda m: literals[int(m.group(1))], text)
        print("   %-30s %d mention(s) in code" % (os.path.basename(path), before))
        if apply:
            io.open(path, "w", encoding="utf-8", newline="\n").write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
