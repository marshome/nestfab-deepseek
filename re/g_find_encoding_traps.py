# -*- coding: utf-8 -*-
"""Find every subprocess call in re/ that takes text WITHOUT naming an encoding, because this machine decodes with GBK.

**THE DEFECT THIS LOOKS FOR IS THE ONE THAT MADE A RULE LIE.** `g_round_output.py` ran a git command with the text flag set and NO encoding named, so Python
decoded git's UTF-8 output with the console codepage -- GBK here. A commit
subject containing any non-ASCII byte made `.stdout` **None**, the next `.strip()` raised, and `rounds-must-land-code` reported "the check did not report a count"
instead of the encoding error underneath. **This project's rules are written in Chinese and land in commit messages, so the trigger is not exotic.**

A call is at risk when it asks for text and does not name an encoding. **`errors="replace"` counts, because it makes the decode total.**
"""
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# **THE PATTERN IS BUILT FROM PIECES SO THIS FILE CANNOT MATCH ITSELF.** The first version wrote the shape as one literal in its docstring, and the detector then
# reported its OWN documentation as a trap -- the same self-match that broke `g_fix_encoding_traps.py`, whose constant was the thing it replaced.
SHAPE = "capture_output" + "=True, text" + "=True"


def has_trap(arguments):
    """True when a call asks for text, does not name an encoding, and is therefore decoded with the CONSOLE CODEPAGE on this machine."""
    if SHAPE not in arguments and "universal_newlines=True" not in arguments:
        return False
    return "encoding=" not in arguments


def main():
    risky = []
    for path in sorted(glob.glob(os.path.join(HERE, "*.py"))):
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in re.finditer(r"subprocess\.(run|check_output|Popen)\s*\(([^)]*)\)", text, re.S):
            arguments = " ".join(match.group(2).split())
            if not has_trap(arguments):
                continue
            line = text[:match.start()].count("\n") + 1
            risky.append((os.path.basename(path), line, arguments[:100]))

    print("subprocess calls that take TEXT without naming an encoding: %d" % len(risky))
    for name, line, arguments in risky:
        print("   %-28s line %-5d %s" % (name, line, arguments))
    if risky:
        print("")
        print("**ON THIS MACHINE THOSE DECODE WITH GBK**, so any non-ASCII byte in the program's output makes `.stdout` None and the caller's next")
        print("attribute access raises -- which is how a rule came to report a missing count instead of an encoding error.")
    return 1 if risky else 0


if __name__ == "__main__":
    sys.exit(main())
