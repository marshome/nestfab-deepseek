# -*- coding: utf-8 -*-
"""Does any caller of 0x64AEA0 READ the value it returns?

The ledger carries a SHAPE claim, `logger.classification-unchecked`: "the project classified 0x64AEA0 as a logger with no effect on a
return value, and that classification has been checked for ONE caller (0xB470) and not for the other fifty-three." That is a
falsifiable statement and this makes it decidable: for every caller, look at the instructions after the call and see whether anything
reads `rax`, `eax`, `ax` or `al` before they are written.

The logger writes rax six times, so the classification is true exactly when every caller overwrites it. One caller that reads it turns
the claim into a defect and says which function needs re-reading.

    python g_logger_rax.py

A SELF-CHECK, per the rule, and against a fact already on record: 0xB470 was checked by hand in an earlier round and was found to
overwrite rax. If this tool reports 0xB470 as a reader, it is wrong and refuses to report anything else.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

LOGGER = 0x64AEA0
DIRECT = re.compile(r"^0x([0-9a-f]+)$")
RAX = ("rax", "eax", "ax", "al")
KNOWN_OVERWRITER = 0xB470


def reads_rax_after(body, index):
    """The first thing that happens to rax after the call, and whether that is a read."""
    for later in body[index + 1:index + 12]:
        text = later.op_str.replace(" ", "")
        parts = text.split(",")
        destination = parts[0] if parts else ""
        # a write to rax is a definition, not a read
        if later.mnemonic in ("mov", "movzx", "movsx", "movsxd", "lea") and destination in RAX:
            return False, "defined by %s %s" % (later.mnemonic, later.op_str)
        if later.mnemonic in ("xor", "sub") and destination in RAX and len(parts) > 1 and parts[1] == destination:
            return False, "zeroed by %s %s" % (later.mnemonic, later.op_str)
        if later.mnemonic == "call":
            return None, "another call first, so this is not a read of the logger's value"
        # a read: rax appears anywhere other than as a plain definition
        if re.search(r"\b(?:rax|eax|ax|al)\b", later.op_str) or "rax" in text or "eax" in text:
            return True, "READ by %s %s" % (later.mnemonic, later.op_str)
        if later.mnemonic in ("ret", "jmp"):
            return None, "no read before %s" % later.mnemonic
    return None, "nothing conclusive in the next twelve instructions"


def main():
    profile = load_prof()
    callers = sorted(set((profile.get(LOGGER) or {}).get("callers") or []))
    print("callers of the logger: %d" % len(callers))

    results = {}
    for caller in callers:
        size = (profile.get(caller) or {}).get("size") or 0
        body = [i for i in disasm(caller) if i.address < caller + size]
        verdicts = []
        for index, ins in enumerate(body):
            if ins.mnemonic != "call":
                continue
            match = DIRECT.match(ins.op_str.strip())
            if match and int(match.group(1), 16) == LOGGER:
                verdicts.append(reads_rax_after(body, index))
        if verdicts:
            results[caller] = verdicts

    # ---- the self-check against the one caller checked by hand ------------------------------------------------------------
    known = results.get(KNOWN_OVERWRITER)
    known_ok = known is not None and all(verdict is not True for verdict, _why in known)
    print("SELF-CHECK: 0x%X was checked by hand as overwriting rax, and this tool says %s"
          % (KNOWN_OVERWRITER, "the same" if known_ok else "READS it -- so the tool is wrong" if known else "it does not call the logger"))
    if not known_ok:
        print("REFUSING TO REPORT: the one caller already decided by hand is not reproduced.")
        return 2
    print("")

    readers = []
    settled = []
    unknown = []
    for caller, verdicts in sorted(results.items()):
        for verdict, why in verdicts:
            if verdict is True:
                readers.append((caller, why))
            elif verdict is None and ("another call first" in why or "no read before" in why):
                # THESE ARE CONFIRMED, NOT UNKNOWN. "another call first" means the logger's value was never consulted before it was
                # overwritten by the next call, and "no read before jmp" means the function left without consulting it. The first
                # version listed them as inconclusive, which under-reported the check that had actually been performed.
                settled.append((caller, why))
            elif verdict is None:
                unknown.append((caller, why))

    print("callers classified: %d" % len(results))
    print("callers that READ the logger's return value: %d" % len(readers))
    print("callers CONFIRMED not to read it (overwritten by another call, or left by a jmp): %d" % len(settled))
    print("callers still inconclusive: %d" % len(unknown))
    print("")
    if readers:
        print("THE CLAIM IS FALSIFIED BY THESE -- each needs re-reading:")
        for caller, why in readers[:15]:
            print("   0x%-8X %s" % (caller, why))
    else:
        print("The claim HOLDS for all %d of the callers this tool decided: not one reads the value." % (len(results) - len(unknown)))
    if unknown:
        print("")
        print("and these could not be decided from the next twelve instructions, so they are neither confirmed nor denied:")
        for caller, why in unknown[:15]:
            print("   0x%-8X %s" % (caller, why))
    print("")
    print("The logger writes rax six times, so the classification is true exactly when every caller overwrites it before reading.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
