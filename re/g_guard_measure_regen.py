# -*- coding: utf-8 -*-
"""Guard the measurement regenerator: it may replace its OWN block and nothing else.

**WHAT IT DESTROYED.** `g_measure_order_run.py` finds the text between `BLOCK_START` ("does Order's MODULE RUN hold together?") and `BLOCK_END`
(`return check::finish("test_recovered");`) and replaces ALL of it. **But the measurement block was INSERTED BEFORE THE FINISH MARKER, so every assertion that
had been appended after it -- Supervisor's, TimerWinImplementation's, the Node family's, the sheet selectors', the two cancellers' -- lived INSIDE that span and
was deleted.** The run removed 217 lines and the gate's `check_recovery` said five classes had no test, **which is how it was noticed rather than because anything
looked wrong.**

**SO THE GUARD IS A LINE COUNT AND A CLASS NAME COUNT.** The regenerator may change the measurement and must not remove a `CHECK(`, a `static_assert` or a
class name that was there before. **That is the same principle as `g_land.py`'s "the field set is unchanged": an edit that can only add or replace its own block
is checked by what it may not remove.**
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "g_measure_order_run.py")

OLD = """    body = body[:start] + BODY.replace("@@ROWS@@", "\\n".join(rows)) + "\\n" + body[end:]
    io.open(TEST, "w", encoding="utf-8", newline="\\n").write(body)
    print("rewrote the measurement with %d field(s), checking ORDER rather than a baked list" % len(rows))
    return 0"""

NEW = """    # **THE GUARD: THE REPLACEMENT MAY NOT REMOVE AN ASSERTION OR A CLASS NAME.**
    #
    # The first version replaced everything between the two markers, and because the measurement block had been inserted BEFORE the finish marker, every
    # assertion appended after it lived inside that span. **One run deleted 217 lines -- Supervisor's, TimerWinImplementation's, the Node family's, the sheet
    # selectors' and the two cancellers' tests -- and the only reason it was caught is that `check_recovery` then said five classes had no test.** A tool that
    # rewrites a span it did not create has to be checked by what the span contains.
    rebuilt = body[:start] + BODY.replace("@@ROWS@@", "\\n".join(rows)) + "\\n" + body[end:]

    def evidence(text):
        return (len(re.findall(r"\\bCHECK\\(", text)),
                len(re.findall(r"\\bstatic_assert\\(", text)),
                len(set(re.findall(r"lcns::(\\w+)", text))))

    before, after = evidence(body), evidence(rebuilt)
    if any(after[index] < before[index] for index in range(3)):
        print("REFUSING: the rewrite would remove evidence. checks %d->%d, static_asserts %d->%d, class names %d->%d"
              % (before[0], after[0], before[1], after[1], before[2], after[2]))
        return 2

    io.open(TEST, "w", encoding="utf-8", newline="\\n").write(rebuilt)
    print("rewrote the measurement with %d field(s), checking ORDER rather than a baked list" % len(rows))
    return 0"""


def main():
    text = io.open(TARGET, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "THE GUARD: THE REPLACEMENT MAY NOT REMOVE" in text:
        print("the guard is already there")
        return 0
    if OLD not in text:
        print("REFUSING: the write block is not as expected")
        for line in text.split("\n"):
            if "io.open(TEST" in line:
                print("   found: %s" % line.strip()[:96])
        return 2
    text = text.replace(OLD, NEW, 1)
    if "import re" not in text:
        text = text.replace("import io", "import io\nimport re", 1)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(text)
    print("g_measure_order_run.py now refuses a rewrite that removes checks, static_asserts or class names")
    return 0


if __name__ == "__main__":
    sys.exit(main())
