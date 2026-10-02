# re/RULES.json -- the human's standing requirements, as conditions a program checks

## Why a JSON file and not prose

Prose in a conversation is forgotten by the next session, and prose in a document is forgotten by a long one. Every rule here
is a CONDITION with a check, and `re/g_rules.py` runs the checks. A rule that cannot be checked is written down as a rule that
cannot be checked rather than dressed up as one, because a rule nobody can enforce is worse than no rule: it produces the
feeling of compliance.

    "id"       a short name, used in the failure message
    "rule"     the human's requirement, in their words
    "check"    how a program decides whether it is met
    "where"    which program runs it
    "since"    when it was given, so a new rule is visibly new

## The rules

```json
[
 {"id": "local-commits-only",
  "rule": "本地提交、不要 push",
  "check": "git push appears in no invocation; every run prints how many commits the tracking branch lacks",
  "where": "re/g_round.py asserts it before every command and prints the count",
  "since": "session start"},

 {"id": "gate-before-commit",
  "rule": "门禁保持全绿",
  "check": "re/gate.ps1 exits zero: build with no warnings, ctest, check_recovery, check_arch, check_embeddings, g_coverage, acceptance",
  "where": "re/gate.ps1",
  "since": "session start"},

 {"id": "never-guess",
  "rule": "不要猜——每条结论都带 RVA",
  "check": "re/ledger.py refuses a claim used above its grade; a name needs ORACLE, a layout needs CONSTRUCTOR",
  "where": "re/ledger.py check",
  "since": "session start"},

 {"id": "forwarded-count-not-guessed",
  "rule": "forwardedCount 绝不能因为猜测而上升",
  "check": "every entry in exports_forwarding.inc has a ledger claim at INSTRUCTION or better",
  "where": "re/g_rules.py",
  "since": "session start"},

 {"id": "sync-every-thirty-rounds",
  "rule": "每30轮和我同步一次",
  "check": "re/g_rounds.py --check exits 4 once thirty rounds have passed without a sync",
  "where": "re/g_rounds.py, and re/g_round.py refuses to start a round on that code",
  "since": "round 538"},

 {"id": "named-fields-by-name",
  "rule": "已经识别出结构体的，那些读写的地方就不要还用偏移值了",
  "check": "no bare offset literal addresses a field the ledger names; re/g_field_offsets.py reports violations",
  "where": "re/g_field_offsets.py",
  "since": "round 540"},

 {"id": "no-regex-churn",
  "rule": "不要用多轮正则反复改同一段代码",
  "check": "a script that rewrites a source file records the block it replaced and is run once; re/g_rules.py lists scripts that rewrote a file twice",
  "where": "re/g_rules.py",
  "since": "round 540, after three passes left unbalanced parentheses"},

 {"id": "widen-before-deepening",
  "rule": "不要局限于一个导出函数或者一个结构体，全面广泛地，找线索，顺藤摸瓜",
  "check": "each round's commit touches a source the previous round did not; re/g_rules.py reports the last ten commits grouped by source",
  "where": "re/g_rules.py",
  "since": "round 529"}
]
```

{"id": "local-backup-not-push",
  "rule": "本地打包备份，不 push：用 git bundle 加输入归档，origin 保持不动",
  "check": "re/g_backup.py writes a verified bundle and a tar of the DLL, the pickles and the re/ tooling, and reports the sha256 of each; the run prints that it did not push",
  "where": "re/RULES.md, added 2026-10-02",
  "since": "round 548"}

{"id": "continuous-work",
  "rule": "授权连续推进，只在每 30 轮或遇到阻塞时汇报",
  "check": "re/g_rounds.py --check exits 4 at thirty rounds without a sync",
  "where": "re/RULES.md, added 2026-10-02",
  "since": "round 548"}

 {"id": "four-conditions-exit-nonzero",
  "rule": "规则要以会失败的程序存在，不是文档里的句子",
  "check": "re/g_rules.py, re/ledger.py check, re/g_rounds.py --check and re/gate.ps1 all exit non-zero when broken",
  "where": "the four programs named in AGENTS.md",
  "since": "round 548"}

 {"id": "push-on-request",
  "rule": "push 只在人类于同一对话中明确要求时进行",
  "check": "re/g_round.py asserts that no git invocation it runs contains push; a push is done by hand and reported",
  "where": "re/g_round.py, and this rule",
  "since": "round 552"}

 {"id": "no-blocking-questions",
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

 {"id": "assertions-are-leads",
  "rule": "断言可用；只有与代码冲突时才不采信（没有冲突就用断言的名字）",
  "check": "re/g_conflict.py reports an ORPHAN: an assertion names order.<field> and nothing else in the module uses that name. Zero orphans means the assertions may be used.",
  "where": "re/g_conflict.py",
  "since": "round 572, refined in 573",
},

 {"id": "oracle-needs-instruction",
  "rule": "断言可以命名字段，但偏移只能由指令确定（名字是词、可查冲突；偏移是位置、断言不含它）",
  "check": "re/g_conflict.py reports the orphans and re/g_stale.py the unanchored offsets",
  "where": "re/g_conflict.py, re/g_stale.py",
  "since": "round 572, refined in 573"},

## What is deliberately NOT a rule here

Things this project has decided it does not reproduce are recorded at their sites, not here: logger calls (`0x64AEA0`, a
toolchain artefact with no effect on a return value) and mutex guards. Library code -- iostreams, locale facets, `num_put`,
`__cxa_guard_*`, `std::shared_ptr` refcounts -- is CLASSIFIED and counted, never reimplemented, and the rule for that lives in
`re/CATEGORIES.md` beside the classification itself.
