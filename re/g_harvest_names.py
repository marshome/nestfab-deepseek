# -*- coding: utf-8 -*-
"""The module's names, harvested from every reporter-family entry point at once.

Usage: python g_harvest_names.py

One oracle is not enough. The module hands strings to several entry points, and each one is a naming channel for everything
that calls it:

    0x60A620  the assertion reporter: condition, method, file          -- 680 callers
    0x82A3E0  the boost assertion: '...: assertion ... failed.'        -- 199 callers
    0x64AEA0  the logger the labels pass already uses                  -- 57 callers
    0x910A60, 0x90D870, 0x7ABEA0, 0x7B2880  the option-key readers: the string IS the option name
    0x600680, 0x5FEF30, 0x5FD0A0  more of the same family

For each call site this recovers the strings the caller hands over, and for each function it collects them into:

    a method name   when a string is a bare identifier and the reporter is an assertion entry
    option keys     when a string is a lower_case_underscore name, which is what this module calls its option and
                    attribute keys
    log lines       when a string is a sentence

Then it walks the call graph and hands every function that has no name of its own the names of the functions it calls,
which is where "one function named, ten identified" comes from. The result is re/NAME_REGISTRY.md plus a summary of how
many functions each channel names.
"""
import io
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import g_leverage as L          # noqa: E402
import g_toolchain as T         # noqa: E402
import lib as LIB               # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

IMAGE = LIB.data if isinstance(LIB.data, (bytes, bytearray)) else LIB.data()
WINDOW = 30
FILE_SUFFIX = (".cpp", ".hpp", ".h", ".cc", ".cxx", ".c", ".inl")
COMPARISON = re.compile(r"[<>=!]|&&|\|\||\bassert\b")
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_:~]*$")
OPTION_KEY = re.compile(r"^[a-z][a-z0-9_]{2,}$")

# The entry points that take strings from their callers. Each is a channel with its own meaning.
#
# Only the assertion and the log channels are kept. An earlier version of this list also carried the option-key readers
# around 0x5052C0, 0x910A60, 0x90D870, 0x7ABEA0, 0x7B2880, 0x600680, 0x5FEF30 and 0x5FD0A0 on the theory that a string
# handed to them is the option name. Running it showed the theory is wrong: those addresses sit in the import stub bank and
# in third party code, and the "names" that came out were 'Modulus', 'ModPrime1PrivateExponent',
# 'N8CryptoPP31DL_GroupParameters_IntegerBasedE' and a 64 character hex literal -- CryptoPP property pages and dynamic
# loading wrappers, not this module's option keys. A channel that cannot be told apart from the loaders is not worth the
# false names it produces, so it is out.
CHANNELS = {
    0x60A620: "assertion",
    0x82A3E0: "assertion",
    0x3B2B0: "assertion",
    0x64AEA0: "log",
    0x7B5B90: "log",
}


def string_at(rva, limit=140):
    try:
        off = rva2off(rva)
    except Exception:
        return None
    if off is None or off < 0 or off >= len(IMAGE):
        return None
    out = []
    for b in IMAGE[off:off + limit]:
        if b == 0:
            break
        if 32 <= b < 127:
            out.append(chr(b))
        else:
            return None
    text = "".join(out)
    return text if len(text) >= 2 else None


def literals_before(body, index, window=WINDOW):
    out = []
    for i in range(max(0, index - window), index):
        ins = body[i]
        m = re.search(r"\[rip [+-] 0x([0-9a-f]+)\]", ins.op_str)
        if not m:
            continue
        disp = int(m.group(1), 16)
        if "[rip - " in ins.op_str:
            disp = -disp
        nxt = body[i + 1].address if i + 1 < len(body) else ins.address + 8
        text = string_at(nxt + disp)
        if text:
            out.append(text)
    return out


def main():
    profile = load_prof()
    reg = defaultdict(lambda: {"methods": set(), "options": set(), "loglines": set(), "sources": set()})

    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        for index, ins in enumerate(body):
            if ins.mnemonic != "call":
                continue
            m = re.search(r"0x([0-9a-f]+)", ins.op_str)
            if not m:
                continue
            callee = int(m.group(1), 16)
            channel = CHANNELS.get(callee)
            if channel is None:
                continue
            texts = literals_before(body, index)
            entry = reg[addr]
            entry["sources"].add(channel)
            # A call site whose window carries several bare identifiers is usually a window that spilled into its
            # neighbour -- the orchestration at 0x2AB0 came out as 'CreateProblem, GetCommonCutProperties' that way. But an
            # assertion legitimately carries a file name next to its method name, and the file is the anchor: when the
            # window has a source file in it, the identifier that sits immediately before that file is the method. Without
            # this rule 100 method names that the first version found were thrown away with the noise.
            files = [i for i, t in enumerate(texts) if t.endswith(FILE_SUFFIX)]
            identifiers = [t for t in texts
                           if IDENTIFIER.match(t) and not COMPARISON.search(t) and not t.endswith(FILE_SUFFIX)]
            picked = None
            if len(identifiers) == 1:
                picked = identifiers[0]
            elif files:
                first_file = files[0]
                for i in range(first_file - 1, -1, -1):
                    if IDENTIFIER.match(texts[i]) and not COMPARISON.search(texts[i]) and not texts[i].endswith(FILE_SUFFIX):
                        picked = texts[i]
                        break
            if channel == "log":
                # The log channel's names are the ones a function loads into the FIRST argument slot -- 'lea rcx, [rip+..]'
                # immediately before the call -- which is the shape every exported entry point has:
                # 0xB1D0 'GenerateHtmlLaunchingOrderReport', 0xB540 'AsyncCancelAllComputationsAndDeleteLaunchingOrder',
                # 0x118F0 'DeleteLaunchingOrder'. 0x2AB0 loads '// LaunchLocalComputation' instead, a comment rather than a
                # function name and a different slot, so requiring the rcx form and rejecting '// ' is what keeps this
                # channel honest. It is the reason this channel names 68 functions and not 157.
                near = None
                for i in range(index - 1, max(-1, index - 6), -1):
                    if body[i].mnemonic == "lea" and body[i].op_str.startswith("rcx,"):
                        m = re.search(r"\[rip [+-] 0x([0-9a-f]+)\]", body[i].op_str)
                        if m:
                            disp = int(m.group(1), 16)
                            if "[rip - " in body[i].op_str:
                                disp = -disp
                            nxt = body[i + 1].address if i + 1 < len(body) else body[i].address + 8
                            near = string_at(nxt + disp)
                        break
                if near and IDENTIFIER.match(near) and not near.startswith("//"):
                    entry["methods"].add(near)
                # and NOTHING else is taken from this call site: without the rcx form above a log call carries no name
                # here, and the first version of this loop fell through to the generic rule and stamped 0x2AB0 with
                # 'GetLayerRestrictedZonePart' -- a name from a callee's own log line. A channel that falls back to the
                # generic rule when its own test fails is not a channel.
                for text in texts:
                    if text.startswith("// "):
                        entry["loglines"].add(text)
                continue
            if picked:
                entry["methods"].add(picked)
            for text in texts:
                if text.endswith(FILE_SUFFIX):
                    continue
                if IDENTIFIER.match(text) and not COMPARISON.search(text):
                    continue
                entry["loglines"].add(text)

    # Everything merged so far is direct evidence. What follows is a HYPOTHESIS and is kept in its own field, because the
    # two must never be added together: a function that has no name of its own is only *described by* what it calls. An
    # earlier version merged hypotheses into the same list, and then 0x2AB0 -- which the module names
    # '// LaunchLocalComputation' in its own log line -- came out as 'ComputeSheetGeometryRowMode', the name of a function
    # it calls. That is the failure mode this separation exists to prevent.
    succ = {}
    for addr, info in profile.items():
        succ[addr] = [c for c in (info.get("callees") or []) if c in profile]
    guesses = defaultdict(set)
    for _round in range(3):
        added = 0
        for addr, callees in succ.items():
            if reg[addr]["methods"]:
                continue
            for c in callees[:40]:
                if reg[c]["methods"]:
                    guesses[addr].add(sorted(reg[c]["methods"])[0])
                    added += 1
                    break
        if not added:
            break

    named = {a: v for a, v in reg.items() if v["methods"] or v["options"]}
    print("functions with a name from a reporter channel: %d" % len(named))
    print("  with a method name : %d" % sum(1 for v in reg.values() if v["methods"]))
    print("  with a log line    : %d" % sum(1 for v in reg.values() if v["loglines"]))
    print("  with only a guessed name from a callee: %d" % len(guesses))
    print("")

    json_path = os.path.join(L.ROOT, "re", "name_registry.json")
    out = {}
    for a in sorted(set(list(reg) + list(guesses))):
        v = reg[a]
        out["0x%X" % a] = {
            "methods": sorted(v["methods"]),
            "loglines": sorted(v["loglines"])[:4],
            "via": sorted(v["sources"]),
            "guessed_from_callees": sorted(guesses.get(a, ()))[:3],
            "size": (profile.get(a) or {}).get("size"),
        }
    io.open(json_path, "w", encoding="utf-8", newline="\n").write(json.dumps(out, indent=1, sort_keys=True))
    print("wrote %s (%d entries)" % (json_path, len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
