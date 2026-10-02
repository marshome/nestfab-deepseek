# -*- coding: utf-8 -*-
"""Wire the set-consistency rule into re/RULES.md and re/g_rules.py."""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "RULES.md")
GRULES = os.path.join(HERE, "g_rules.py")

RULE = """ {"id": "counts-need-consistent-rows",
  "rule": "一个计数只有在它所数的那些行彼此一致时，才能支持关于其中之一的断言",
  "check": "re/g_set_consistency.py -- run on the rows behind a count, it REFUSES when the members disagree. It cannot inspect a claim on its own, and says so: the failure is invisible in a number and visible only in the rows.",
  "where": "re/g_set_consistency.py",
  "since": "round 627"},
"""

CHECK = '''

def check_counts_need_consistent_rows():
    """Every tool that prints a per-row breakdown must be self-testable, and the checker must refuse disagreeing rows.

    The rule comes from three failures in five rounds -- a closure of 596 for a four-function job, `lea reg,[base+0x40]` finding 1955
    where the ledger said 15, and a 0x50 element address counted 57 times across four different field sets. Each count was arithmetically
    correct and answered a different question from the one the claim was about.

    What this can check is whether the CHECKER works: its own self-test must refuse the rows that produced the element50 count and accept
    a set that agrees. Whether any particular claim has consistent rows is not visible here, and the rule says so rather than implying
    coverage it does not have.
    """
    code, out, _err = run([sys.executable, os.path.join(HERE, "g_set_consistency.py")])
    if code != 0:
        return "FAIL", "the set-consistency checker's own self-test did not pass: %s" % out.strip().splitlines()[-1:]
    if "REFUSED" not in out:
        return "FAIL", "the checker did not refuse the rows known to disagree, so it cannot be trusted"
    return "PASS", ("its self-test refuses the disagreeing rows and accepts agreeing ones; whether a given claim's rows agree is not "
                    "visible to this check")
'''


def main():
    text = io.open(RULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "counts-need-consistent-rows" not in text:
        marker = "## What is deliberately NOT a rule here"
        text = text.replace(marker, RULE.rstrip("\n") + "\n\n" + marker, 1)
        io.open(RULES, "w", encoding="utf-8", newline="\n").write(text)
        print("re/RULES.md: the rule added")

    rules = io.open(GRULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "check_counts_need_consistent_rows" not in rules:
        rules = rules.replace("def check_rules_have_checks():", CHECK.strip("\n") + "\n\n\ndef check_rules_have_checks():", 1)
        rules = rules.replace(
            '    ("goal-drives-continuation", "用持久化目标驱动连续推进", check_goal_drives_continuation),',
            '    ("goal-drives-continuation", "用持久化目标驱动连续推进", check_goal_drives_continuation),\n'
            '    ("counts-need-consistent-rows", "计数需要行一致", check_counts_need_consistent_rows),', 1)
        io.open(GRULES, "w", encoding="utf-8", newline="\n").write(rules)
        print("re/g_rules.py: the check wired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
