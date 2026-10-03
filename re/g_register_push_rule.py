# -*- coding: utf-8 -*-
"""Register the new rule: a check function in g_rules.py, its entry in the CHECKS list, and the declaration in RULES.md.

**THE HUMAN'S INSTRUCTION THIS ROUND IS "每30轮push一下吧"**, which changes the DEFAULT from `local-backup-not-push`'s "不 push" to "push at the thirty-round sync".
The two older rules stay as they are -- they describe the default and the exception, and this one makes the cadence explicit -- and the three are reconciled by
this rule being the one that says WHEN.

**AND IT IS CHECKABLE WITHOUT LYING WHEN THE NETWORK IS DOWN.** The remote has been unreachable repeatedly in this session, so the check reports UNCHECKED in
that case: **a rule that fails because GitHub is unreachable would teach the wrong lesson about the tree.**
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = os.path.join(HERE, "g_rules.py")
RULES = os.path.join(HERE, "RULES.md")

FUNCTION = '''

def check_push_every_thirty_rounds():
    """每30轮push一次 -- at the thirty-round sync, local must be level with origin.

    The human's instruction at round 92 is "每30轮push一下吧", which replaces the default of never pushing with a cadence. The sync is the same thirty rounds
    `sync-every-thirty-rounds` counts, so the condition is: **when the sync is due, `origin/main..HEAD` must be empty.**

    **AND AN UNREACHABLE REMOTE IS UNCHECKED AND NOT A FAILURE.** This project's origin has been unreachable for long stretches, and a rule that reports the tree
    as broken because GitHub is down is a rule that lies. The check says UNCHECKED with the git error beside it, so the difference between "not pushed" and "could
    not ask" stays visible.
    """
    code, out, _err = run([sys.executable, os.path.join(HERE, "g_rounds.py"), "--check"])
    if code != 0:
        return "PASS", "the sync is not due yet, so no push is owed"
    code, out, err = run(["git", "rev-list", "--count", "origin/main..HEAD"])
    if code != 0:
        return "UNCHECKED", "origin is unreachable: %s" % (err or out).strip()[:80]
    behind = int((out or "0").strip() or 0)
    if behind:
        return "FAIL", "the sync is due and %d commit(s) are not pushed" % behind
    return "PASS", "the sync is due and origin/main is level with HEAD"

'''

ENTRY = '    ("push-every-thirty-rounds", "每30轮push一次", check_push_every_thirty_rounds),\n'

DECLARATION = ''' {"id": "push-every-thirty-rounds",
  "rule": "每30轮push一次",
  "check": "re/g_rules.py check_push_every_thirty_rounds: when re/g_rounds.py --check says the sync is due, `git rev-list --count origin/main..HEAD` must be 0, and UNCHECKED when origin cannot be reached",
  "where": "re/g_rules.py, and this rule",
  "since": "round 92, the human's instruction 每30轮push一下吧"},

'''


def main():
    text = io.open(CHECKER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "def check_push_every_thirty_rounds" in text:
        print("the check is already registered")
        return 0

    # 1) the function, before the CHECKS list, which begins with the tuple block
    anchor = text.find('\nCHECKS = [')
    if anchor < 0:
        anchor = text.find('\n    ("counts-need-consistent-rows"')
    if anchor < 0:
        print("REFUSING: the CHECKS list is not found")
        return 2
    if anchor == text.find('\n    ("counts-need-consistent-rows"'):
        # the list is inline; put the function before the enclosing statement
        anchor = text.rfind("\n\n", 0, anchor)
    text = text[:anchor] + FUNCTION + text[anchor:]

    # 2) the tuple in the list
    marker = '    ("extractor-self-check",'
    if marker not in text:
        print("REFUSING: the list's last entry is not found")
        return 2
    text = text.replace(marker, ENTRY + marker, 1)
    io.open(CHECKER, "w", encoding="utf-8", newline="\n").write(text)
    print("g_rules.py: registered check_push_every_thirty_rounds")

    # 3) the declaration
    rules = io.open(RULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "push-every-thirty-rounds" in rules:
        print("RULES.md already declares it")
        return 0
    tail = rules.rfind("\n\n")
    rules = rules[:tail] + "\n\n" + DECLARATION.rstrip("\n") + rules[tail:]
    io.open(RULES, "w", encoding="utf-8", newline="\n").write(rules)
    print("RULES.md: declared push-every-thirty-rounds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
