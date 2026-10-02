# -*- coding: utf-8 -*-
"""Downgrade every claim that rests on an assertion string alone, and record the risk as a rule.

The human's warning: an assertion's text and the code it sits in may not agree, because the code can be updated while the
assertion is not. That is not hypothetical, and this project already has one instance of exactly that failure mode -- a comment in
launching_order.hpp quotes a constant at 0x9DE958, and that address does not exist in the module.

So an assertion string is a LEAD and not a proof, and every claim whose only witness is one must say so. The ledger's grades
already have the right shape for this: `ORACLE` means "the module's own words", which is strong evidence for a NAME but says
nothing about whether the assertion is still TRUE. A name from a stale assertion is a name that may belong to a field that was
renamed or removed.

This adds a distinct claim for the risk rather than editing the grades, because the grades are not wrong -- an oracle IS good
evidence for a name -- and what is missing is the second step: a name from an oracle needs an INSTRUCTION witness for the field
it names, and until it has one the field's offset is unconfirmed.

The concrete consequence for the four names found last round:

    common_cut_safety_preference     +0x6C   ALSO has a setter witness (RE 0xEA09/0xEA0D), so it stands
    multitorch_cutting_preference    +0x9C   ALSO has a setter witness (RE 0xF225/0xF233), so it stands
    parts                                     no offset, no field witness -- a lead
    sheets                                    no offset, no field witness -- a lead

so the warning does not weaken the two that were already named from setters; it makes precise which of the four are proved and
which are leads.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

RULES = r"D:\Nesting\nestfab\re\RULES.md"

ADDITION = """ {"id": "assertions-are-leads",
  "rule": "断言里的信息可能和实际代码不一致——代码更新了断言没更新，所以断言只作线索，不作证明",
  "check": "every claim whose witness is an assertion STRING must also carry an INSTRUCTION witness for the offset it names; re/g_stale.py lists the ones that do not",
  "where": "re/g_stale.py, and re/LEDGER.md's grade table",
  "since": "round 572",
},

 {"id": "oracle-needs-instruction",
  "rule": "名字可以从 oracle 来，但字段的偏移必须另有指令级见证",
  "check": "re/g_stale.py compares each ORACLE name against the instruction witnesses in the ledger",
  "where": "re/g_stale.py",
  "since": "round 572"},
"""


def main():
    text = io.open(RULES, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "assertions-are-leads" not in text:
        marker = "## What is deliberately NOT a rule here"
        text = text.replace(marker, ADDITION.rstrip("\n") + "\n\n" + marker, 1)
        io.open(RULES, "w", encoding="utf-8", newline="\n").write(text)
        print("re/RULES.md: two rules added about stale assertions")
    else:
        print("re/RULES.md already has them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
