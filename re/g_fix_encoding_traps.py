# -*- coding: utf-8 -*-
"""Give every subprocess call in re/ an explicit encoding, because this machine decodes with GBK.

**THE TRIGGER IS THIS PROJECT'S OWN RULES.** They are written in Chinese, they land in commit messages, and the tools read git's output -- so a `text=True` call
without an `encoding` decodes UTF-8 bytes with GBK, `.stdout` becomes None, and the caller's next attribute access raises. **That is how `rounds-must-land-code`
came to report "the check did not report a count" instead of the encoding error beneath it**, which is a rule lying about the tree.

**AND `g_rules.py` WAS ONE OF THE TEN**, so the checker that runs every other check could die on a bilingual verdict.

**THE REPLACEMENT IS ONE STRING AND IT IS THE SAME IN EVERY CALL**: `text=True` becomes
`text=True, encoding="utf-8", errors="replace"`. `errors="replace"` is deliberate: a tool that reads git output must not be able to fail on a byte, and a
replacement character is visible in the verdict if it ever matters.
"""
import glob
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# **AND THE PATTERN IS ONE SEARCH FOR THE CALLS THAT LACK AN ENCODING.** The version this replaces wrote the OLD text as a literal and then REPLACED ITSELF,
# producing `OLD = "capture_output=True, text=True, encoding="utf-8", errors="replace""` -- an unterminated string, because the tool's own constant was a match
# for the tool's own search. **A bulk replacement that can match the pattern it is built from will rewrite its own definition**, which is the same shape as a
# regex that crosses a newline: the tool has to be built so its own text cannot be the thing it edits.
MARKER = "capture_output=True"
ENCODING = 'encoding="utf-8", errors="replace"'


def main():
    changed = []
    for path in sorted(glob.glob(os.path.join(HERE, "*.py"))):
        name = os.path.basename(path)
        if name in ("g_find_encoding_traps.py", "g_fix_encoding_traps.py"):
            continue                      # these two HOLD the pattern rather than making a call with it
        text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        # **THE GUARD THE FIRST VERSION LACKED: ONLY A CALL THAT DOES NOT ALREADY NAME AN ENCODING.** Without it, calls that had one got a second, and fourteen
        # files -- including all five planted-defect proofs, which then exited 1 with no output -- died on `keyword argument repeated`.
        fixed, count = [], 0
        for line in text.split("\n"):
            if MARKER in line and ENCODING not in line and "text=True" in line:
                line = line.replace(MARKER, MARKER + ", " + ENCODING)
                count += 1
            fixed.append(line)
        if not count:
            continue
        io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(fixed))
        changed.append((name, count))

    for name, count in changed:
        print("   %-28s %d call(s)" % (name, count))
    print("%d file(s) changed" % len(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
