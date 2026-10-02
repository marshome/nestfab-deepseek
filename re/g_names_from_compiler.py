# -*- coding: utf-8 -*-
"""Get the correct qualified names from the COMPILER rather than from a parser.

Two attempts at walking the generated header's namespace nesting got the depth wrong, and the compiler knew the right answer both times:
"'AllSheetSelector' is not a member of 'lcns'; did you mean 'lcns::Multi::AllSheetSelector'?". So this reads the build log, takes the
compiler's suggestion for each of the test's pointer declarations, and rewrites them.

**A parser that reproduces a structure badly is worth less than a tool that reports its own disagreement**, and the compiler is that tool.
"""
import io
import os
import re

ROOT = r"D:\Nesting\nestfab"
LOG = os.path.join(ROOT, "lcns", "build", "gate_build.log")
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")


def main():
    log = io.open(LOG, encoding="utf-8", errors="replace").read()
    # every "did you mean 'X::Y'" gives the name the compiler knows
    fixes = {}
    for match in re.finditer(r"'(\w+)' is not a member of '([\w:]+)'; did you mean '([\w:]+)'", log):
        short, wrong_ns, right = match.group(1), match.group(2), match.group(3)
        fixes[(wrong_ns, short)] = right
    print("the compiler named %d correct qualified names" % len(fixes))
    for (wrong_ns, short), right in list(fixes.items())[:8]:
        print("   %s::%s  ->  %s" % (wrong_ns, short, right))
    if not fixes:
        print("no suggestions in the log; nothing to rewrite")
        return 0

    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    changed = 0
    for (wrong_ns, short), right in fixes.items():
        # the test declares them as `lcns::Foo* pN = nullptr;` inside the generated block
        old = "lcns::%s* p" % short
        new = "%s* p" % right
        if old in text:
            text = text.replace(old, new)
            changed += 1
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote %d declarations from the compiler's answers" % changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
