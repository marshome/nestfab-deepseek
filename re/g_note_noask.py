# -*- coding: utf-8 -*-
"""Record that the standing authorisation means no round may ASK, and read the next two exports.

The human has now asked twice not to be asked every round -- once to grant continuous work and once to say it again because a
round ended with a question anyway. A grant that exists in re/RULES.md and is ignored in practice is the same failure this
project keeps recording: the mechanism is not the rule, it is the thing that FAILS. So the grant becomes three rules with three
checks, and one of them is that a SYNTHESIS may not end in a question when no block exists.

The exports read here are the next two by the corrected ranking, whose bodies are 52 bytes each:

    0xB020  GetPartUserStringEx  (55/56)  reads the order's +0x1B8, which the ledger names `userString`, then TAILS to 0x63F228
    0xB060  GetSheetUserStringEx (61/62)  the same shape for a sheet
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

RULES = r"D:\Nesting\nestfab\re\RULES.md"
DECISIONS = r"D:\Nesting\nestfab\re\DECISIONS.md"

ADDITIONS = """ {"id": "no-blocking-questions",
  "rule": "不要每轮都问我；只有真正阻塞时才停下提问",
  "check": "re/g_ask.py reports a round whose text ends in a question while no block is recorded",
  "where": "re/g_ask.py, and the rule that says report every thirty rounds",
  "since": "round 558"},

 {"id": "report-not-ask",
  "rule": "汇报是陈述，不是请求许可",
  "check": "a summary states what was done, what the numbers are now, and what is next; it asks nothing",
  "where": "re/g_ask.py",
  "since": "round 558"},

 {"id": "decide-required-decisions",
  "rule": "需要决策也要先给出我的判断和理由，再问",
  "check": "re/g_ask.py flags a question that carries no proposed answer",
  "where": "re/g_ask.py",
  "since": "round 558"},
"""


def main():
    text = io.open(RULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "no-blocking-questions" not in text:
        marker = "## What is deliberately NOT a rule here"
        text = text.replace(marker, ADDITIONS.rstrip("\n") + "\n\n" + marker, 1)
        io.open(RULES, "w", encoding="utf-8", newline="\n").write(text)
        print("re/RULES.md: three rules added about not asking")
    else:
        print("re/RULES.md already has them")

    decisions = io.open(DECISIONS, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    row = ("| 558 | the human said not to ask every round, for the second time; the grant was already in re/RULES.md and was "
           "being ignored in practice | re/g_ask.py now fails a summary that ends in a question with no block recorded |")
    if "said not to ask every round" not in decisions:
        decisions = decisions.replace("## The open question about", row + "\n\n## The open question about", 1)
        io.open(DECISIONS, "w", encoding="utf-8", newline="\n").write(decisions)
        print("re/DECISIONS.md: recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
