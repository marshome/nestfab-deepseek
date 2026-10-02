# -*- coding: utf-8 -*-
"""Make the named-but-undeclared check precise, then report the sync.

THE FALSE POSITIVE, found while gathering the sync's numbers: the count went from 17 to 20 and all three new rows were headers that mention a
class declared ELSEWHERE -- vtable_layout.hpp mentions Engine::InfiniteEngine, class_constructors.hpp and nesting_nester_fields.hpp mention
Multi::NestingNester. **Those are correct cross-references, not over-claims**, and a check that penalises them will be ignored.

So the test is now: a class is a real over-claim only when NO hand-written header declares it. A header that names a class declared in another
header is doing what headers are for.
"""
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TARGET = os.path.join(HERE, "g_defined_classes.py")


def main():
    text = io.open(TARGET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    marker = "    print(\"HEADERS THAT NAME A CLASS MORE THAN ONCE WITHOUT DECLARING IT: %d\" % len(overclaims))"
    if "declared_somewhere" in text:
        print("already precise")
        return 0
    if marker not in text:
        print("REFUSING: the reporting marker moved, so the patch cannot be placed reliably")
        return 2

    patch = '''    # A CROSS-REFERENCE IS NOT AN OVER-CLAIM. A header that names a class DECLARED IN ANOTHER header is doing what headers are for, so the
    # defect is narrower than "named more than once here and not declared here": it is "named more than once and declared NOWHERE", which is
    # what a reader can mistake for a definition. The first version conflated the two and flagged three correct cross-references.
    declared_somewhere = set()
    for path, text_of in headers.items():
        for match in re.finditer(r"\\b(?:class|struct)\\s+(\\w+)", text_of):
            declared_somewhere.add(match.group(1))
    overclaims = [row for row in overclaims if row[1].split("::")[-1] not in declared_somewhere]

'''
    text = text.replace(marker, patch + marker, 1)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("g_defined_classes.py now excludes cross-references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
