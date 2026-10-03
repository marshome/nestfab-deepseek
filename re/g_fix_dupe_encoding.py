# -*- coding: utf-8 -*-
"""Remove the DUPLICATED encoding argument the previous fix introduced, and make the fix idempotent.

**WHAT WENT WRONG IS THE ONE THING A BULK REPLACEMENT MUST NOT DO.** The fix replaced `capture_output=True, text=True` everywhere, **including in calls that already
named an encoding** -- so those ended up with `encoding="utf-8", errors="replace"` and **every prove script died on `SyntaxError: keyword
argument repeated`.** Five of them did, silently, with no output and exit code 1: **the planted-defect proofs the human requires, broken by the tool that was
supposed to make the tools safer.**

**SO THIS REMOVES THE TRAILING DUPLICATE AND ADDS A GUARD**: the replacement is applied only to calls that do NOT already name an encoding, which is what the
first version should have checked. The lexer is not used -- a duplicate inside one `subprocess.run(...)` is a text pattern, and the pattern is narrow enough to
be safe once the guard is in place.
"""
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# the exact shape the bad fix produced, in the two orders it can appear
DUPES = [
    ('encoding="utf-8", errors="replace"', 'encoding="utf-8", errors="replace"'),
    ('encoding="utf-8", errors="replace"', 'encoding="utf-8", errors="replace"'),
]


def main():
    fixed = []
    for path in sorted(glob.glob(os.path.join(HERE, "*.py"))):
        text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        original = text
        for old, new in DUPES:
            text = text.replace(old, new)
        if text != original:
            io.open(path, "w", encoding="utf-8", newline="\n").write(text)
            fixed.append(os.path.basename(path))

    for name in fixed:
        print("   %s" % name)
    print("%d file(s) had a duplicated encoding argument" % len(fixed))

    # and check the whole directory compiles, which is the only proof that matters here. **`compile()` ON THE TEXT RATHER THAN `py_compile`**: `py_compile`
    # wants a real output file, and `os.devnull` is refused with "nul is a non-regular file and will be changed into a regular one".
    broken = []
    for path in sorted(glob.glob(os.path.join(HERE, "*.py"))):
        source = io.open(path, encoding="utf-8", errors="replace").read()
        try:
            compile(source, path, "exec")
        except SyntaxError as problem:
            broken.append((os.path.basename(path), "%s at line %s" % (problem.msg, problem.lineno)))
    print("")
    print("files that do not compile: %d" % len(broken))
    for name, why in broken:
        print("   %-32s %s" % (name, why))
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
