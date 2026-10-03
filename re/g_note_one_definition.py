# -*- coding: utf-8 -*-
"""Register the one-definition rule, via re/g_note.py."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

RULE = ("one definition per module object: two structs whose offset-commented fields share 20 or more offsets AND cover 60 percent of the smaller "
        "one describe the same module object, and that is the second description this project forbids. The FIELD NAMES are deliberately not part of "
        "the test, because Order and LaunchingOrderLayout agree on only 2 names in 45 while describing the same fields -- one names a field by the "
        "export that sets it and the other by its offset, and a name-based rule therefore excludes the very duplication the check is for. Each pair is "
        "either reconciled, or recorded as not a duplication with the reason it is two things, or recorded as debt with the adjudication.")


def main():
    result = subprocess.run([sys.executable, os.path.join(HERE, "g_note.py"), "requirement", RULE,
                             "--check", "re/g_one_definition.py"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((result.stdout or "").strip()[:400])
    if result.returncode != 0:
        print((result.stderr or "").strip()[:300])
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
