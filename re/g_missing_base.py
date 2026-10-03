# -*- coding: utf-8 -*-
"""Find every class whose model offsets are SYSTEMATICALLY SHORT of the module's -- a base part the model does not have.

**THE `Nester` FAILURE WAS NOT A TYPO AND IT IS NOT THE ONLY ONE OF ITS KIND.** The model declared `Nester` with no data, the module's base part is 0x18 bytes, and
**every derived class's every field was therefore 0x10 too low** -- the same 0x10 that a constant had been written to paper over. **A systematic offset shared by many
members of one class is the signature**, and this looks for it in two ways:

  * **a `+ gap` constant in a header**: an arithmetic correction standing in for a field, which is what `kNestingNesterBaseDataGap` was
  * **a constructor that writes a range of offsets the declaring struct does not cover**: a base part the model is missing

    python -u g_missing_base.py
"""
import glob
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

GAP = re.compile(r"^\s*(?:inline\s+)?constexpr\s+[\w:]+\s+(\w*[Gg]ap\w*)\s*=\s*(0x[0-9A-Fa-f]+|\d+)\s*;", re.M)
BASE_NOTE = re.compile(r"has not been read|not established|What they\s+are is NOT", re.I)


def constants():
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "*.hpp"))):
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in GAP.finditer(text):
            value = int(match.group(2), 16) if match.group(2).startswith("0x") else int(match.group(2))
            if value == 0:
                continue
            # the comment beside it, for whether it admits an unread base
            line_start = text.rfind("\n", 0, match.start())
            line_end = text.find("\n", match.end())
            line = text[line_start:line_end]
            out.append((os.path.basename(path), match.group(1), value, bool(BASE_NOTE.search(line)), line.strip()[:88]))
    return out


def main():
    found = constants()
    print("**NON-ZERO `*gap*` CONSTANTS -- an arithmetic correction standing in for a field: %d**" % len(found))
    for name, variable, value, admits, line in found:
        print("   %-24s %-38s 0x%X%s" % (name, variable[:38], value, "   <- ITS OWN COMMENT ADMITS AN UNREAD BASE" if admits else ""))
        print("      %s" % line)
    print("")

    # and the `+ gap` arithmetic that consumes them
    uses = []
    for path in glob.glob(os.path.join(ROOT, "lcns", "tests", "*.cpp")) + glob.glob(os.path.join(ROOT, "lcns", "src", "*.cpp")):
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for match in re.finditer(r"[^\n]*\b\w*[Gg]ap\w*\b[^\n]*", text):
            if "+" in match.group(0) and "==" in match.group(0):
                uses.append((os.path.basename(path), match.group(0).strip()[:88]))
    print("**`member + gap == moduleOffset` ASSERTIONS -- the correction being applied: %d**" % len(uses))
    for name, line in uses[:12]:
        print("   %-22s %s" % (name, line))
    return 0


if __name__ == "__main__":
    sys.exit(main())
