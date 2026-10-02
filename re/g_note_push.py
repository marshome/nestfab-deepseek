# -*- coding: utf-8 -*-
"""Record that a push happened on request, and that the rule is now "push when asked" rather than "never".

The default stays the same and the mechanism that protects it is unchanged: re/g_round.py asserts that no git invocation it
makes contains `push`, so no round can push by accident. What changed is that the human asked for one in the conversation, which
is what the rule's own text always allowed -- "never push UNLESS the human asked for a push in that same conversation". Before
this round nothing had ever been pushed: 65 commits existed only on this disk, which is why re/g_backup.py was built. Now
origin/main is at the same commit as HEAD, so the exposure is closed from both ends, a local bundle AND the remote.

The check for `local-backup-not-push` is widened rather than weakened: a backup is satisfied by EITHER a recent verified bundle
OR a HEAD that origin already has, because both make the commits survive the disk. A rule that demanded a bundle after the
remote already had everything would be a rule that fails on a healthy repository, and a check that always fails is a check
nobody reads.
"""
import io
import re

RULES = r"D:\Nesting\nestfab\re\RULES.md"
DECISIONS = r"D:\Nesting\nestfab\re\DECISIONS.md"


def main():
    text = io.open(RULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    text = text.replace('{"id": "local-backup-not-push",\n  "rule": "本地打包备份，不 push",',
                        '{"id": "local-backup-not-push",\n  "rule": "本地打包备份；push 仅在人类当次要求时进行",')
    if "pushed on request" not in text:
        marker = "## What is deliberately NOT a rule here"
        addition = (' {"id": "push-on-request",\n'
                    '  "rule": "push 只在人类于同一对话中明确要求时进行",\n'
                    '  "check": "re/g_round.py asserts that no git invocation it runs contains push; a push is done by hand '
                    'and reported",\n'
                    '  "where": "re/g_round.py, and this rule",\n'
                    '  "since": "round 552"}\n\n')
        text = text.replace(marker, addition + marker, 1)
    io.open(RULES, "w", encoding="utf-8", newline="\n").write(text)

    decisions = io.open(DECISIONS, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    row = ("| 552 | the human asked for a push, so 65 commits went to origin/main; the default stays local | "
           "git branch shows main at origin/main, ahead 0 behind 0 |")
    if "the human asked for a push" not in decisions:
        decisions = decisions.replace("## The open question about", row + "\n\n## The open question about", 1)
    io.open(DECISIONS, "w", encoding="utf-8", newline="\n").write(decisions)
    print("rule and decision updated: push on request, local otherwise")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
