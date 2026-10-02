# -*- coding: utf-8 -*-
"""Names whose only witness is an assertion string, against names that also have an instruction.

Usage: python g_stale.py [--fix]

The human's warning made concrete: an assertion's text may not match the code it sits in, because the code can change while the
assertion does not. This project has one instance already -- a comment in launching_order.hpp quotes a constant at 0x9DE958 and no
such address exists in the module -- so the risk is real and not theoretical.

The ledger's grades are not wrong: an ORACLE is genuinely strong evidence for a NAME. What is missing is the second step, and this
tool performs it. For every name the ledger holds, it asks whether the same name also has an INSTRUCTION witness, and reports the
ones that do not:

    a name with an oracle AND an instruction    proved: the assertion says what the field is called and a store says it is there
    a name with an oracle ONLY                  a LEAD: the name may be current and the field may have moved or gone

The distinction matters because the two cases need different next actions. A proved name can be written into a header today; a
lead needs its offset found first, and writing it into a header on the assertion's word alone is the guess this project's whole
ledger exists to refuse.

`--fix` downgrades the oracle-only names to SHAPE in re/ledger.json, which is what they are.
"""
import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import ledger  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "ledger.json")


def main(argv):
    fix = "--fix" in argv
    data = ledger.load()
    claims = data["claims"]

    # every offset that has an INSTRUCTION witness, from the claims whose predicate quotes an address
    proved_offsets = set()
    for claim in claims:
        if claim["grade"] not in ("INSTRUCTION", "MEASURED", "CONSTRUCTOR", "DIFFERENTIAL"):
            continue
        for m in re.finditer(r"\+0x([0-9A-Fa-f]+)", claim.get("predicate", "") + " " + claim.get("witness", "")):
            proved_offsets.add(int(m.group(1), 16))
    # and every RE address any claim at INSTRUCTION or better quotes, which is a second way a name is anchored
    proved_addresses = set()
    for claim in claims:
        if claim["grade"] not in ("INSTRUCTION", "MEASURED", "CONSTRUCTOR", "DIFFERENTIAL"):
            continue
        for m in re.finditer(r"0x([0-9A-Fa-f]{4,7})", claim.get("witness", "")):
            proved_addresses.add(int(m.group(1), 16))

    oracle_only = []
    proved = []
    for claim in claims:
        if claim["grade"] != "ORACLE":
            continue
        subject = claim["subject"]
        predicate = claim.get("predicate", "")
        witness = claim.get("witness", "")
        # FUNCTION names and FIELD names are anchored in different ways, and the first version of this tool conflated them,
        # reporting GetBuildDate and GetMajorVersion as leads when each has a logger string at its OWN entry address:
        #
        #   a function name is anchored by an address, because the string sits in the function it names
        #   a field name is anchored by an OFFSET, because the name has to be tied to a position in an object
        #
        # so the two cases get their own rules rather than one rule with a false positive in it.
        is_function = ("ordinal" in predicate or "rva" in predicate or subject.startswith("export.")
                       or "function" in predicate.lower())
        offsets = [int(m.group(1), 16) for m in re.finditer(r"\+0x([0-9A-Fa-f]+)", predicate + " " + witness)]
        addresses = [int(m.group(1), 16) for m in re.finditer(r"0x([0-9A-Fa-f]{4,7})", witness)]
        if is_function:
            anchored = bool(addresses)
        else:
            anchored = bool(offsets) and any(o in proved_offsets for o in offsets)
        if anchored:
            proved.append(subject)
        else:
            oracle_only.append(claim)

    print("ORACLE claims: %d" % (len(proved) + len(oracle_only)))
    print("    anchored by an offset or an RE address in their own witness: %d" % len(proved))
    print("    a lead, with no offset and no address:                        %d" % len(oracle_only))
    print("")
    if oracle_only:
        print("LEADS -- an assertion names these and nothing has confirmed where they are:")
        for claim in oracle_only:
            print("    %-34s %s" % (claim["subject"][:34], claim["predicate"][:80]))
        print("")
    print("A proved name can be written into a header today. A lead needs its offset found first, and writing it into a header on")
    print("the assertion's word alone is the guess the ledger exists to refuse.")

    if fix and oracle_only:
        for claim in oracle_only:
            claim["grade"] = "SHAPE"
            claim["witness"] = (claim.get("witness", "") + "  [DOWNGRADED to SHAPE: an assertion string is a lead, because the "
                                "code can be updated while the assertion is not]")
        ledger.save(data)
        print("")
        print("re/ledger.json: %d claim(s) downgraded from ORACLE to SHAPE" % len(oracle_only))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
