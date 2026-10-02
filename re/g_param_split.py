# -*- coding: utf-8 -*-
"""Split the identifier-like lookup strings into PARAMETERS and DATA, using the store as the test.

The previous round found that the 175-name figure included MIPLIB benchmark names -- air03, bell3a, danoint, egout -- so a `lea` of a
rip-relative string before a lookup does not make that string a parameter name. The distinguishing test is already recorded in the data:
**a parameter's lookup result is STORED into a field, and a datum is not.**

    python g_param_split.py [--table]

Output: re/param_split.json, and with --table a C++ table of the confirmed names.

A SELF-CHECK, per the rule, against two facts already established: `nesting_pow_boost` is a parameter (it lands at rsi+0x100, read by
hand) and `air03` is not (it is a MIPLIB instance). If either is on the wrong side, the split is wrong.
"""
import argparse
import collections
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib as LIB           # noqa: E402
from lib import rva2off     # noqa: E402

IDENT = re.compile(r"^[a-z][a-z0-9_]{4,}$")
SELF_CHECK_PARAMETER = "nesting_pow_boost"
SELF_CHECK_DATA = "air03"


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", action="store_true")
    args = parser.parse_args(argv)

    blob = LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data
    data = json.loads(io.open(os.path.join(HERE, "param_fields2.json"), encoding="utf-8").read())

    stored = collections.Counter()
    seen = collections.Counter()
    sites = collections.defaultdict(set)
    for function, rows in data["sites"].items():
        for row in rows:
            rva = row.get("name_rva")
            if not rva:
                continue
            offset = rva2off(int(rva, 16))
            if offset is None:
                continue
            stop = blob.find(b"\x00", offset)
            if stop <= offset:
                continue
            name = blob[offset:stop].decode("ascii", "replace")
            if not IDENT.match(name):
                continue
            seen[name] += 1
            if row.get("base") and row["base"] != "rsp" and row.get("offset"):
                stored[name] += 1
                sites[name].add(function)

    parameters = sorted(name for name in seen if stored[name] > 0)
    data_names = sorted(name for name in seen if stored[name] == 0)

    ok_parameter = SELF_CHECK_PARAMETER in parameters
    ok_data = SELF_CHECK_DATA in data_names
    print("SELF-CHECK: %s is a parameter? %s   %s is data? %s"
          % (SELF_CHECK_PARAMETER, ok_parameter, SELF_CHECK_DATA, ok_data))
    if not (ok_parameter and ok_data):
        print("REFUSING TO REPORT: the split puts a known parameter or a known datum on the wrong side.")
        return 2
    print("")

    print("identifier-like strings before a lookup: %d" % (len(parameters) + len(data_names)))
    print("  STORED into a field, so PARAMETERS: %d" % len(parameters))
    print("  NOT stored, so DATA or an unplaced name: %d" % len(data_names))
    print("")
    print("the data-looking strings, which the previous round's count wrongly included:")
    for name in data_names[:24]:
        print("   %s" % name)
    print("")
    if args.table:
        print("the confirmed parameters, as a table:")
        for name in parameters:
            print('    {"%s", %d, %d},' % (name, seen[name], stored[name]))
        print("")

    payload = {"parameters": {n: {"seen": seen[n], "stored": stored[n], "functions": sorted(sites[n])}
                              for n in parameters},
               "data": data_names}
    io.open(os.path.join(HERE, "param_split.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(payload, indent=1, sort_keys=True))
    print("wrote re/param_split.json")
    print("")
    print("The test is the STORE and not the string: a lookup whose result is written into a field is a parameter, and a name that is")
    print("merely loaded before a lookup is a datum. That is why the previous count was too high, and it is why this one states both.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
