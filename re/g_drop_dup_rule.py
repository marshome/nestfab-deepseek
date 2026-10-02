# -*- coding: utf-8 -*-
"""Merge the two rules re/g_note.py just wrote for the same requirement into the one that names its check.

I ran the command twice: once without `--check`, which recorded a rule "with no check yet", and once with it, which recorded the same rule under
a different id. **TWO RULES FOR ONE REQUIREMENT IS THE DUPLICATION THIS PROJECT HAS A CHECK FOR**, and re/g_duplicates.py exists to find it, so
the checkless one goes.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "RULES.md")
DROP = "re-vtables-json-vtable-null-typeinfo-0xa"


def main():
    text = io.open(RULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    # remove the JSON object whose id is the checkless duplicate
    pattern = re.compile(r'\n?\{"id":\s*"%s",.*?"since":\s*"[^"]*"\}\n?' % re.escape(DROP), re.S)
    found = pattern.search(text)
    if not found:
        print("the checkless duplicate is not present")
        return 0
    text = text[:found.start()] + "\n" + text[found.end():]
    io.open(RULES, "w", encoding="utf-8", newline="\n").write(text)
    print("removed the checkless duplicate %s" % DROP)
    remaining = re.findall(r'\{"id":\s*"([^"]+)"', text)
    print("%d rules remain" % len(remaining))
    return 0


if __name__ == "__main__":
    sys.exit(main())
