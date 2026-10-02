# -*- coding: utf-8 -*-
"""Every assertion in the module whose condition names a field or an accessor.

RE 0x60A620's sites load up to three strings: the condition, the method and the file. The previous round decoded one function's seven
sites and got `quality >= 0 && quality < 9`, `GetLayerLeatherSheet`, `../structure/border_property.hpp` and
`boost.find(order.multitorch_cutting_preference) != boost.end()`. This runs the same decode over every site in the module.

    python g_assert_names.py [--top 40] [--grep <regex>]
Output: re/assert_names.json

ONLY THE LOADED FORM IS DECODED, and that is a stated limit rather than an oversight: some sites build the string from immediates and
some load it, the previous round established both, and generalising from one is what defeated an earlier attempt. Sites of the built
form come out as absent and are counted separately, so the tool reports coverage rather than implying it.

A SELF-CHECK, per the rule: 0x1EE50's line-649 site must yield the string naming multitorch_cutting_preference, because that is the
decode this tool generalises from.
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
from lib import disasm, load_prof, rva2off  # noqa: E402

REPORTER = 0x60A620
DIRECT = re.compile(r"^0x([0-9a-f]+)$")
LEA_RIP = re.compile(r"^[a-z0-9]+, \[rip \+ (0x[0-9a-f]+)\]$")
LINE_REG = re.compile(r"^(edx|r8d|ecx|r9d), (0x[0-9a-f]+)$")
SELF_CHECK = "multitorch_cutting_preference"


def image():
    return LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data


def string_at(rva, blob):
    offset = rva2off(rva)
    if offset is None or offset < 0 or offset >= len(blob):
        return None
    end = blob.find(b"\x00", offset)
    if end < 0 or end - offset > 400 or end == offset:
        return None
    raw = blob[offset:end]
    printable = sum(1 for byte in raw if 32 <= byte < 127 or byte == 9)
    if printable < len(raw) * 0.9:
        return None
    return raw.decode("ascii", "replace")


def sites(address, profile, blob):
    size = (profile.get(address) or {}).get("size") or 0
    body = [i for i in disasm(address) if i.address < address + size]
    out = []
    for index, ins in enumerate(body):
        if ins.mnemonic != "call":
            continue
        match = DIRECT.match(ins.op_str.strip())
        if not match or int(match.group(1), 16) != REPORTER:
            continue
        line = None
        strings = []
        for back in range(index - 1, max(-1, index - 40), -1):
            previous = body[back]
            text = previous.op_str.strip()
            if previous.mnemonic == "call":
                continue
            if previous.mnemonic == "lea":
                moved = LEA_RIP.match(text)
                if moved:
                    target = previous.address + previous.size + int(moved.group(1), 16)
                    found = string_at(target, blob)
                    if found:
                        strings.append(found)
                continue
            moved = LINE_REG.match(text)
            if moved and line is None:
                line = int(moved.group(2), 16)
        out.append((ins.address, line, list(reversed(strings))))
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=40)
    parser.add_argument("--grep", default=None)
    args = parser.parse_args(argv)
    profile = load_prof()
    blob = image()

    # ---- the self-check against the site this tool generalises from ------------------------------------------------------
    check = [entry for entry in sites(0x1EE50, profile, blob) if entry[1] == 649]
    found = check and any(SELF_CHECK in text for text in check[0][2])
    print("SELF-CHECK: 0x1EE50 line 649 yields a string naming %s?  %s" % (SELF_CHECK, bool(found)))
    if not found:
        print("REFUSING TO REPORT: the site this decode generalises from is not reproduced.")
        return 2
    print("")

    callers = sorted(set((profile.get(REPORTER) or {}).get("callers") or []))
    payload = {}
    named = 0
    built_form = 0
    total = 0
    for address in callers:
        entries = sites(address, profile, blob)
        if not entries:
            continue
        rows = []
        for at, line, strings in entries:
            total += 1
            if strings:
                named += 1
            else:
                built_form += 1
            rows.append({"site": "0x%X" % at, "line": line, "strings": strings})
        payload["0x%X" % address] = rows
    io.open(os.path.join(HERE, "assert_names.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps({"sites": payload}, indent=1, sort_keys=True))

    print("functions with reporter calls: %d" % len(payload))
    print("sites: %d, of which %d yield a loaded string and %d are of the built form" % (total, named, built_form))
    print("")

    # THE THREE KINDS OF STRING, told apart by shape rather than by position: a FILE ends in a source extension, a CONDITION contains
    # an operator or a call, and anything else is a METHOD name. The first version lumped files in with conditions because a path
    # contains dots and slashes.
    files = collections.Counter()
    methods = collections.Counter()
    conditions = collections.Counter()
    for rows in payload.values():
        for row in rows:
            for text in row["strings"]:
                if re.search(r"\.(cpp|hpp|h|c|cc|cxx)$", text):
                    files[text] += 1
                elif any(op in text for op in ("==", "!=", ">=", "<=", "&&", "||", "(", " < ", " > ")):
                    conditions[text] += 1
                elif re.match(r"^[A-Za-z_][A-Za-z0-9_:~]*$", text):
                    methods[text] += 1

    print("=== the FILES the module's assertions live in (%d distinct)" % len(files))
    for text, count in files.most_common(16):
        print("   x%-3d %s" % (count, text))
    print("")
    print("=== the METHODS that assert (%d distinct)" % len(methods))
    for text, count in methods.most_common(16):
        print("   x%-3d %s" % (count, text))
    print("")

    if args.grep:
        pattern = re.compile(args.grep)
        conditions = collections.Counter({k: v for k, v in conditions.items() if pattern.search(k)})
    print("=== the CONDITIONS that name something (%d distinct)" % len(conditions))
    print("")
    for text, count in conditions.most_common(args.top):
        print("   x%-3d %s" % (count, text[:130]))
    print("")
    print("wrote re/assert_names.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
