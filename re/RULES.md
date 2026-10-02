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

## What is deliberately NOT a rule here

Things this project has decided it does not reproduce are recorded at their sites, not here: logger calls (`0x64AEA0`, a
toolchain artefact with no effect on a return value) and mutex guards. Library code -- iostreams, locale facets, `num_put`,
`__cxa_guard_*`, `std::shared_ptr` refcounts -- is CLASSIFIED and counted, never reimplemented, and the rule for that lives in
`re/CATEGORIES.md` beside the classification itself.
