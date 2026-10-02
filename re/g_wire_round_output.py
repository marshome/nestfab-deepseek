# -*- coding: utf-8 -*-
"""Register the round-output rule: a window of rounds must be landing C++ under lcns/."""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "RULES.md")
GRULES = os.path.join(HERE, "g_rules.py")

RULE = """ {"id": "rounds-must-land-code",
  "rule": "一轮不能只有分析；窗口内的提交必须落地 lcns/ 下的 C++",
  "check": "re/g_round_output.py exits 1 when fewer than four of the last twelve commits touched lcns/. It measures a WINDOW and not a round, because it runs after a commit and cannot know which round it belongs to -- and it says so",
  "where": "re/g_round_output.py",
  "since": "round 642"},
"""

CHECK = '''

def check_rounds_must_land_code():
    """A window of recent rounds must be landing C++ under lcns/, not only analysis.

    The human said "the recovered C++ is so little, where are you stuck", and the measurement agreed: rounds 500-549 filed 27 ledger
    claims while layout.hpp's 3744 lines were committed around rounds 141-173, and the recent fifty rounds filed 87 claims against about
    1500 lines. **The measurement infrastructure had grown until it consumed the product.** A rule is the response because that is this
    project's only mechanism that works.

    What this can measure is the window, not the round: it runs after a commit and cannot know which round that commit belongs to. The
    check prints that limitation rather than implying a per-round guarantee.
    """
    code, out, _err = run([sys.executable, os.path.join(HERE, "g_round_output.py")])
    landed = None
    for line in out.split("\\n"):
        m = re.search(r"commits that landed C\\+\\+ under lcns/:\\s*(\\d+) of\\s*(\\d+)", line)
        if m:
            landed = (int(m.group(1)), int(m.group(2)))
    if landed is None:
        return "FAIL", "the round-output check did not report a count, so it cannot be trusted"
    if code != 0:
        return "FAIL", "%d of the last %d commits landed C++ under lcns/, below the floor of 4" % landed
    return "PASS", ("%d of the last %d commits landed C++ under lcns/; this measures a WINDOW and not whether any given round wrote "
                    "code" % landed)
'''


def main():
    text = io.open(RULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "rounds-must-land-code" not in text:
        marker = "## What is deliberately NOT a rule here"
        text = text.replace(marker, RULE.rstrip("\n") + "\n\n" + marker, 1)
        io.open(RULES, "w", encoding="utf-8", newline="\n").write(text)
        print("re/RULES.md: the rule added")

    rules = io.open(GRULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "check_rounds_must_land_code" not in rules:
        rules = rules.replace("def check_rules_have_checks():", CHECK.strip("\n") + "\n\n\ndef check_rules_have_checks():", 1)
        rules = rules.replace(
            '    ("counts-need-consistent-rows", "计数需要行一致", check_counts_need_consistent_rows),',
            '    ("counts-need-consistent-rows", "计数需要行一致", check_counts_need_consistent_rows),\n'
            '    ("rounds-must-land-code", "每轮必须落地代码", check_rounds_must_land_code),', 1)
        io.open(GRULES, "w", encoding="utf-8", newline="\n").write(rules)
        print("re/g_rules.py: the check wired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
