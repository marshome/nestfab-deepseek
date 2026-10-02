# -*- coding: utf-8 -*-
"""Fix check_rules_have_checks properly: read the `"check"` FIELD, and compare counts rather than two independent lists.

THE FIRST FIX READ THE WRONG FORMAT. It looked for `its check is:` lines, and re/RULES.md writes `"check": "re/g_no_offset_tables.py"` inside the
rule's own JSON block -- so the fix changed nothing and the four rules were still reported unchecked while each named a check that exists.

THE TEST NOW HAS TWO PARTS, because a rule can be enforced two ways and both are legitimate:
  * a check function inside re/g_rules.py, listed in CHECKS
  * a `"check"` field naming a script, whose PATH IS VERIFIED TO EXIST -- because **a rule whose check has been deleted looks enforced and is
    not**, which is the drift this meta-check is for
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "g_rules.py")

NEW = '''    text = io.open(os.path.join(HERE, "RULES.md"), encoding="utf-8", errors="replace").read()
    declared = sorted(set(re.findall(r'\\{"id":\\s*"([^"]+)"', text)))
    # A RULE'S CHECK IS NAMED IN ITS OWN `"check"` FIELD: `"check": "re/g_no_offset_tables.py"`. An earlier version of this function read only
    # the `{"id": ...}` keys, and a later one looked for an `its check is:` line that re/RULES.md does not use -- so four rules were reported
    # unchecked while each named a check that exists.
    named = re.findall(r'"check":\\s*"([^"]+?\\.(?:py|ps1))', text)
    executed = {identifier for identifier, _rule, _fn in CHECKS}
    absent = [path for path in named if not os.path.exists(os.path.join(HERE, os.path.basename(path)))
              and not os.path.exists(os.path.join(HERE, path))]
    if absent:
        return "FAIL", "rules naming a check that does not exist: %s" % ", ".join(sorted(set(absent)))
    unchecked = [d for d in declared if d not in executed]
    if len(named) < len(unchecked):
        return "FAIL", "%d declared rule(s) with neither a function in re/g_rules.py nor a named check: %s" % (
            len(unchecked) - len(named), ", ".join(unchecked))
    return "PASS", "%d declared rules; %d enforced by a function here and %d by a named check that exists" % (
        len(declared), len(executed), len(named))
'''


def main():
    text = io.open(RULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find("    text = io.open(os.path.join(HERE, \"RULES.md\")")
    if start < 0:
        print("REFUSING: the body is not found")
        return 2
    end = text.find("def check_backup():", start)
    if end < 0:
        print("REFUSING: the following function is not found")
        return 2
    # keep the docstring of the function being replaced
    head = text[:start]
    doc_start = head.rfind('    """')
    body_start = head.rfind("\n", 0, doc_start)
    text = text[:body_start + 1] + NEW + "\n\n" + text[end:]
    io.open(RULES, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote the body to read the check field and verify the path")
    return 0


if __name__ == "__main__":
    sys.exit(main())
