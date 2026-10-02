# -*- coding: utf-8 -*-
"""Record that a persistent GOAL is the mechanism for running many rounds, and that it was missing.

The human pointed out that the web interface can run dozens of rounds without being asked, and they are right: `create_goal`
persists an objective and the session CONTINUES automatically until the objective is met or the goal's round cap is reached. This
project had been running one round per human message for a hundred rounds, which is why every round ended with a summary and a
question.

That is the same class of mistake the whole session keeps finding, now in the mechanics rather than the analysis: **the capability
existed, nobody used it, and the symptom looked like a limitation of the interface.** The rule that follows is worth stating
because it generalises: before concluding that something cannot be done, check whether the harness offers a mechanism for it.

What this writes:
  * a rule in re/RULES.md whose check is that a goal exists and is armed
  * the decision, with the round it was learned
  * and a note that the goal's objective carries the working rules, so an automatic continuation reads them rather than relying on
    the conversation
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "RULES.md")
DECISIONS = os.path.join(HERE, "DECISIONS.md")

RULE = """ {"id": "goal-drives-continuation",
  "rule": "用持久化目标驱动连续推进，而不是每轮等人类说话",
  "check": "a goal is armed and its objective restates the working rules, so an automatic continuation reads them from the goal rather than from the conversation",
  "where": "the harness's goal mechanism, and this file",
  "since": "round 581"},
"""


def main():
    text = io.open(RULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "goal-drives-continuation" not in text:
        marker = "## What is deliberately NOT a rule here"
        text = text.replace(marker, RULE.rstrip("\n") + "\n\n" + marker, 1)
        io.open(RULES, "w", encoding="utf-8", newline="\n").write(text)
        print("re/RULES.md: the goal rule added")
    else:
        print("re/RULES.md already has it")

    decisions = io.open(DECISIONS, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    row = ("| 581 | a persistent GOAL is what makes the session continue without being asked; a hundred rounds had been run one "
           "per human message | the human pointed out that the web interface runs dozens of rounds unprompted; create_goal had "
           "never been used |")
    if "persistent GOAL is what makes" not in decisions:
        decisions = decisions.replace("## The open question about", row + "\n\n## The open question about", 1)
        io.open(DECISIONS, "w", encoding="utf-8", newline="\n").write(decisions)
        print("re/DECISIONS.md: recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
