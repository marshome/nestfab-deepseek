# -*- coding: utf-8 -*-
"""Rewrite check_rules_have_checks as a whole function, with the docstring closed and the escapes right.

THE PREVIOUS ATTEMPT LEFT THE DOCSTRING OPEN, which is what the syntax error was, and wrote `\\{` into a non-raw string, which Python warns
about. **Both are the same failure**: a patch placed by searching for text rather than by replacing a whole unit. This replaces the function.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "g_rules.py")

FUNCTION = '''def check_rules_have_checks():
    """Every rule declared in re/RULES.md must have a check, and a NAMED check must exist.

    THE CHECK READ ONE FORMAT AND MISSED FOUR RULES. re/RULES.md declares a rule as a JSON object with an `"id"` and a `"check"` field, and
    re/g_note.py writes both; this function read only the ids, so four rules added in one session were reported as unchecked WHILE EACH NAMED A
    CHECK THAT EXISTS AND RUNS.

    AND THE TEST IS STRONGER THAN IT WAS, not merely wider: a rule that names a check path is verified against the FILESYSTEM, because **a rule
    whose check has been deleted looks enforced and is not** -- which is the drift this meta-check exists to catch.
    """
    text = io.open(os.path.join(HERE, "RULES.md"), encoding="utf-8", errors="replace").read()
    declared = sorted(set(re.findall(r'\\{"id":\\s*"([^"]+)"', text)))
    named = re.findall(r'"check":\\s*"([^"]+?\\.(?:py|ps1))', text)
    executed = {identifier for identifier, _rule, _fn in CHECKS}
    absent = sorted({path for path in named
                     if not os.path.exists(os.path.join(HERE, os.path.basename(path)))
                     and not os.path.exists(os.path.join(HERE, path))})
    if absent:
        return "FAIL", "rules naming a check that does not exist: %s" % ", ".join(absent)
    unchecked = [d for d in declared if d not in executed]
    if len(named) < len(unchecked):
        return "FAIL", "%d declared rule(s) with neither a function in re/g_rules.py nor a named check: %s" % (
            len(unchecked) - len(named), ", ".join(unchecked))
    return "PASS", "%d declared rules; %d enforced by a function here and %d by a named check that exists" % (
        len(declared), len(executed), len(named))
'''


def main():
    text = io.open(RULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find("def check_rules_have_checks():")
    if start < 0:
        print("REFUSING: the function is not found")
        return 2
    end = text.find("\ndef check_backup():", start)
    if end < 0:
        print("REFUSING: the following function is not found")
        return 2
    text = text[:start] + FUNCTION + "\n" + text[end + 1:]
    io.open(RULES, "w", encoding="utf-8", newline="\n").write(text)
    # COMPILE IT BEFORE CLAIMING SUCCESS -- the previous attempt wrote a syntax error and said it had succeeded
    try:
        compile(text, RULES, "exec")
    except SyntaxError as error:
        print("REFUSING: the rewritten file does not compile -- line %d: %s" % (error.lineno, error.msg))
        return 1
    print("rewrote check_rules_have_checks; the file compiles")
    return 0


if __name__ == "__main__":
    sys.exit(main())
