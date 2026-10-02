# AGENTS.md -- the standing instructions for this workspace

`re/RESUME.md`, `re/RULES.md` and `re/DECISIONS.md` are the domain rules, the checked requirements and the dated decisions.

**This file is deliberately a POINTER and not a copy.** DSH loads it automatically on the first request of every session in this
workspace (the `dsh-agent-instructions` chain: `$DSH_HOME/AGENTS.md`, then every existing candidate from the project root -- the
`.git` marker -- down to the working directory). A copy of the rules here would be a second version that drifts, and drift
between two copies of one rule is the exact failure `re/g_duplicates.py` was written to catch. So: read the files, do not
restate them.

`re/RESUME.md`、`re/RULES.md`、`re/DECISIONS.md` 是本项目的领域规则、可检查的要求和带日期的决定。**本文件是索引，不是副本。**
DSH 在每次会话的第一条请求就自动加载本文件（`dsh-agent-instructions` 链：先 `$DSH_HOME/AGENTS.md`，再从项目根——以 `.git` 为标记
——逐级向下到工作目录的每个候选文件）。把规则抄到这里会形成第二份、会漂移的版本，而"同一条规则的两份拷贝不一致"正是
`re/g_duplicates.py` 被写出来要抓的失败。

## Read these, in this order, before any work

1. **`re/RESUME.md`** -- the rules of the project and a checkpoint: `forwardedCount`, what is implemented, what is half-read,
   and how the work is counted.
2. **`re/RULES.md`** -- the human's standing requirements, each with the program that CHECKS it. A rule with no check says so;
   it is never dressed up as enforced.
3. **`re/DECISIONS.md`** -- every requirement and every decision, with the round it was given. A new instruction is visibly new
   here, and an old one is visibly old.
4. **`re/LEDGER.md`** and `re/ledger.json` -- what the project believes, and the grade of evidence behind each belief.
5. **`re/AGENT.md`** -- the six components of the loop and what each is for.

## The loop, in one paragraph

Choose a task from `re/g_prioritize.py` (which reads `re/ledger.json`), run its extractor, read the result and decide what it
establishes, record the claim with its grade, write the C++ or the document, run `re/gate.ps1` and require it green, commit
locally with the addresses in the message, then `re/g_rounds.py --done "..."`. A round that begins from the conversation instead
of from the ranking is the drift this repository is built to prevent.

## The four conditions that fail rather than warn

    re/g_rules.py                 the human's requirements, checked; exits non-zero when one breaks
    re/ledger.py check            no claim used above the grade its witness supports
    re/g_rounds.py --check        exits 4 once thirty rounds have passed without a sync with the human
    re/gate.ps1                   build with no warnings, 22 tests, and five checks; must be green before a commit

## What not to do

* **Never `git push`.** Local commits only. `re/g_round.py` asserts it before every command it runs.
* **Never name a field or fix a layout on a shape that matches.** A name needs an oracle (the module's own string) or a setter
  whose name is the field's; a layout needs a constructor. See `re/LEDGER.md` for the grades.
* **Never restate a rule from this file in a second place.** Add it to `re/RULES.md` with its check via
  `python re/g_note.py requirement "..."`, or it will drift.
* **Never commit with the gate red**, and never let `forwardedCount` rise on a guess.
