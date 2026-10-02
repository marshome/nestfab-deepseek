# -*- coding: utf-8 -*-
"""Record the reporting cadence and the live checkpoint in re/RESUME.md, so both survive a fresh session.

The human asked for a sync every 30 rounds instead of a report per round. That is a working instruction and it belongs in
the repository rather than in a session, because the next session cannot see this conversation.

The checkpoint is the part that matters most for a handover: which numbers are current, what is implemented, what is
half-read, and the one rule that decides when a name may be used.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
PATH = os.path.join(ROOT, "re", "RESUME.md")

RULES = """
7. **Report every thirty rounds, not every round.** Work continuously between syncs; a round is one batch of work (a read, a
   classification, an implementation, a tool). Keep going until thirty have accumulated, then write one summary that says
   what moved, what the numbers are now, and what is next. The gate and the local commit still happen every round.
"""

CHECKPOINT = """
## Checkpoint (round 538)

| measure | value | where |
|---|---|---|
| `forwardedCount()` | **40 of 168** | `lcns/include/lcns/detail/exports_forwarding.inc` |
| embedded blocks | 205 / 95533 bytes, all matching | `re/EMBEDDED.md` |
| tests | 22 of 22, 116 of 116 acceptance checks | `re/gate.ps1` |
| domain functions named by the reporter channels | 251 read from their own call sites, 281 guessed and kept apart | `re/NAME_REGISTRY` -> `re/name_registry.json` |
| this module's classes | **75**, from RTTI | `re/CLASSES.md` |
| LaunchLocalComputation closure | 7 functions, 6636 bytes | `re/LAUNCH_LOCAL_COMPUTATION.md` |

Implemented in this stretch, each with its evidence and its test:

* the launch order's layout, 0x2C0 bytes and 96 fields, read out of `0x14620 NewLaunchingOrder` -- `lcns/include/lcns/launching_order.hpp`
* the 0x48 byte node's copy and release, `0x9302C0` and `0x9308C0`, with the ownership rule the instructions gave --
  `lcns/include/lcns/cns_node.hpp`
* nine exports in one batch, all setters whose closures were empty: `SetOrigin` (86), `SetCommonCutCuttingPreference` (154),
  `CNS_SetMultiplicityPreference` (128), `SetAutomaticStop` (140), `SetCommonCutSafetyPreference` (150),
  `SetMultiTorchCuttingPreference` (176), `SetSpecificSheetOrigin` (298), `SetSpecificSheetObjective` (300) and `SetMarkMode`
  (246) -- `lcns/src/exports_impl.cpp`, and `test_exports.cpp` asserts every store

The rule that decides when a NAME may be used, which cost several rounds to get right:

* a field is named only when the module names it: an export that sets it, an accessor of at most 0x100 bytes that touches
  exactly that one offset and is named, or a serialiser key paired by its VALUE FLOW (key -> the accessor -> the argument the
  JSON constructor receives). Two independent witnesses are preferred and the count is recorded next to each name.
* twenty-six of the launch order's 96 fields clear that bar. The rest keep an offset-derived name (`unnamedXXX`) and the
  header says why. A plausible name with one weak witness is worse than a placeholder, because it hides the gap.

The three data sources that are open but not finished:

* the serialisers -- `..\\structure\\text_io.cpp`, `ToJson` at 0x50DB70, `LoadSheet` 0x5091B0, `LoadCommonCutEvaluation`
  0x509A40. The key vocabulary is recovered; the key-to-offset pairing needs the value flow, not the nearest accessor.
* the Multi vtables -- `re/CLASSES.md` lists them; the twelve strategies' `Run` bodies are the biggest single gap in this
  project and their classes are now identifiable.
* `re/g_class_sites.py` -- where each class is constructed, needing one more step: attribute a construction site by vtable
  ADDRESS rather than by class name, since two classes can share a name.
"""


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    changed = False
    if "Report every thirty rounds" not in text:
        marker = "6. Scripts go in files under `re/`, never inline in a shell command."
        assert marker in text, "rule 6 is gone"
        # append rule 7 just before the next blank-line-terminated section
        end = text.index("\n\n", text.index(marker))
        text = text[:end] + "\n" + RULES.rstrip("\n") + text[end:]
        changed = True
    if "## Checkpoint (round 538)" not in text:
        marker = "## What to tell a fresh session"
        assert marker in text, "the closing section is gone"
        text = text.replace(marker, CHECKPOINT.strip("\n") + "\n\n" + marker, 1)
        changed = True
    if changed:
        io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
        print("updated re/RESUME.md")
    else:
        print("already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
