# -*- coding: utf-8 -*-
"""Fix the rule ids the note tool generated from Chinese text, and add the check each new rule needs.

re/g_note.py derives a rule's id from its text with `[^a-z0-9]+ -> -`, which on Chinese text collapses to almost nothing: the
requirement "授权连续推进，只在每 30 轮或遇到阻塞时汇报" produced the id "30". An id of "30" is a rule nobody can read in a
failure message, so the two new rules get names by hand, and the check for the second one is added because the requirement names
it.
"""
import io

PATH = r"D:\Nesting\nestfab\re\RULES.md"


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    text = text.replace('{"id": "push-git-bundle-origin",', '{"id": "local-backup-not-push",')
    text = text.replace('{"id": "30",', '{"id": "continuous-work",')
    marker = "## What is deliberately NOT a rule here"
    addition = (' {"id": "four-conditions-exit-nonzero",\n'
                '  "rule": "规则要以会失败的程序存在，不是文档里的句子",\n'
                '  "check": "re/g_rules.py, re/ledger.py check, re/g_rounds.py --check and re/gate.ps1 all exit non-zero when '
                'broken",\n'
                '  "where": "the four programs named in AGENTS.md",\n'
                '  "since": "round 548"}\n\n')
    if "four-conditions-exit-nonzero" not in text:
        text = text.replace(marker, addition + marker, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("rule ids corrected and the fourth condition recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
