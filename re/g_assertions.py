# -*- coding: utf-8 -*-
"""Harvest the module's assertions into a naming oracle: function -> (file, method, condition).

Usage: python g_assertions.py [reporter-rva] [out.md]

0x60A620 is the assertion reporter. Its own literals are '*** INTERNAL ERROR: please contact support ***', ': error ' and
'(assertion failed in ', and 679 distinct functions call it 1083 times. Each call site hands it a condition, a method name
and a file name, and those three strings can be recovered in two ways:

    0x733A  rdx -> 0x9AC430  'external_number < map->result.size()'   ; a literal in the image
    0x734E  rdx -> 0x9AC7B8  'GetRing'
    0x7362  rdx -> 0x9AC455  'cns_no_fit.cpp'

    ... and where the string is too short to be worth a table entry, the compiler builds it in registers:
    movabs rdx, 0x69746c756d5c2e2e  ; '..\\multi'    then  '\\marker.'  then  'cp'  = '..\\multi\\marker.cpp'

So a function that nothing else names can still be named, because it asserts on its own name and its own translation unit.
This writes re/NAMES.md: one row per assertion-bearing function with its file, its method, and the condition each call site
checks, plus which of those functions this project has already implemented, verified or classified.

The complementary tool is re/g_tu_map.py, which maps translation units over the whole reachable set. This one is the other
half: the function-to-name pairs, from the call sites.
"""
import io
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
from g_stack_strings import ALIAS, STORE, WIDTH, LOAD, decode  # noqa: E402

IMAGE = LIB.data if isinstance(LIB.data, (bytes, bytearray)) else LIB.data()
WINDOW = 40
FILE_SUFFIX = (".cpp", ".hpp", ".h", ".cc", ".cxx", ".c", ".inl")
COMPARISON = re.compile(r"[<>=!]|&&|\|\||\bassert\b")


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
    return text if len(text) >= 3 else None


def rip_literals(body, index, window=WINDOW):
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
            out.append((ins.address, text))
    return out


def stack_strings_before(body, index, window=WINDOW):
    """The stack-built strings in the window, with the length loaded before the call."""
    out = []
    pending = {}
    text = ""
    start = None
    base = None
    for i in range(max(0, index - window), index):
        ins = body[i]
        mload = LOAD.match(ins.op_str) if ins.mnemonic in ("mov", "movabs") else None
        if mload and not ins.op_str.startswith("["):
            width = 8 if ins.mnemonic == "movabs" else 4
            pending[ALIAS.get(mload.group(1), mload.group(1))] = (int(mload.group(2), 0), width)
            continue
        mstore = STORE.match(ins.op_str) if ins.mnemonic.startswith("mov") else None
        if mstore:
            register = ALIAS.get(mstore.group(4), mstore.group(4))
            this_base = mstore.group(2)
            if register in pending:
                value, _lw = pending.pop(register)
                if start is None:
                    start, base = ins.address, this_base
                if this_base == base:
                    text += decode(value, WIDTH[mstore.group(1)])
                continue
            continue
        if text and ins.mnemonic in ("call", "jmp", "ret"):
            out.append((start, text))
            start, base, text = None, None, ""
    if text:
        out.append((start, text))
    return out


def classify(texts):
    """(file, method, conditions) out of the strings a call site carries."""
    files, methods, conditions = [], [], []
    for text in texts:
        bare = text.strip()
        if bare.endswith(FILE_SUFFIX) and "\\" in bare or bare.endswith(FILE_SUFFIX) and "/" in bare:
            files.append(bare)
        elif bare.endswith(FILE_SUFFIX):
            files.append(bare)
        elif COMPARISON.search(bare) or " " in bare or bare != text:
            conditions.append(text)
        elif re.match(r"^[A-Za-z_][A-Za-z0-9_:~]*$", bare):
            methods.append(bare)
        else:
            conditions.append(text)
    return (files[-1] if files else None, methods[-1] if methods else None, conditions)


def main(argv):
    reporter = int(argv[0], 0) if argv else 0x60A620
    out_path = argv[1] if len(argv) > 1 else os.path.join(L.ROOT, "re", "NAMES.md")
    profile = load_prof()
    sites = defaultdict(list)
    for addr, info in profile.items():
        size = info.get("size") or 0
        if size <= 0:
            continue
        body = [i for i in disasm(addr) if i.address < addr + size]
        for index, ins in enumerate(body):
            if ins.mnemonic != "call":
                continue
            m = re.search(r"0x([0-9a-f]+)", ins.op_str)
            if not m or int(m.group(1), 16) != reporter:
                continue
            texts = [t for _a, t in rip_literals(body, index)]
            texts += [t for _a, t in stack_strings_before(body, index) if t not in texts]
            fname, method, conds = classify(texts)
            sites[addr].append((ins.address, fname, method, conds[0] if conds else None))

    named = {a: v for a, v in sites.items() if any(x[2] for x in v)}
    files = defaultdict(set)
    for a, v in named.items():
        for _c, f, _m, _cond in v:
            if f:
                files[f].add(a)

    lines = ["# The names the assertions carry",
             "",
             "Generated by `re/g_assertions.py` from the %d call sites of the assertion reporter `0x%X` in %d functions."
             % (sum(len(v) for v in sites.values()), reporter, len(sites)),
             "A call site hands the reporter a condition, a method name and a file name, so this is the module's own record",
             "of which function is which, read out of the call sites rather than guessed from the bodies. The translation",
             "unit map over the whole reachable set is `re/TU_MAP.md`; this file is the function-to-name half of it.",
             "",
             "| | |",
             "|---|---:|",
             "| call sites | %d |" % sum(len(v) for v in sites.values()),
             "| functions that assert | %d |" % len(sites),
             "| functions whose method name was recovered | %d |" % len(named),
             "| translation units named | %d |" % len(files),
             ""]
    for fname in sorted(files):
        lines.append("## %s" % fname)
        lines.append("")
        lines.append("| method | function | call site | condition |")
        lines.append("|---|---|---:|---|")
        for a in sorted(files[fname]):
            for call_addr, _f, method, cond in sites[a]:
                if not method:
                    continue
                note = ""
                if a in T.BOILERPLATE:
                    note = " (boilerplate)"
                elif a in getattr(T, "IMPLEMENTED", ()):
                    note = " (implemented here)"
                elif a in L.VERIFIED:
                    note = " (verified here)"
                lines.append("| `%s` | `0x%X`%s | 0x%X | %s |"
                             % (method, a, note, call_addr,
                                ("`%s`" % cond.replace("|", "\\|")[:110]) if cond else "&mdash;"))
        lines.append("")
    leftover = {a: v for a, v in sites.items() if a not in named}
    if leftover:
        lines.append("## functions that assert but whose method name was not recovered")
        lines.append("")
        for a in sorted(leftover):
            texts = ", ".join("`%s`" % c[3] if c[3] else "?" for c in leftover[a][:2])
            lines.append("* `0x%X`: %d call site(s), conditions %s" % (a, len(leftover[a]), texts))
        lines.append("")
    io.open(out_path, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("0x%X: %d call sites in %d functions" % (reporter, sum(len(v) for v in sites.values()), len(sites)))
    print("recovered a method name for %d functions, across %d translation units" % (len(named), len(files)))
    print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
