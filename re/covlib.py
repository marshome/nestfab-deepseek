# -*- coding: utf-8 -*-
"""Shared analysis helpers for the coverage / TU-map tools.

Keeping the reachability and citation logic in ONE place matters: these two tools must agree on
what "reachable" and "cited" mean, otherwise the progress numbers drift apart.
"""
import glob
import io
import json
import os
import re
import sys
from collections import Counter, deque

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402

RE = r"D:\Nesting\nestfab\re"
LC = r"D:\Nesting\nestfab\lcns"

PROF = load_prof()
TOTAL_BYTES = sum((v.get("size") or 0) for v in PROF.values())


def export_addrs():
    out = []
    for e in EXPORTS:
        a = None
        if isinstance(e, (list, tuple)):
            for v in e:
                if isinstance(v, int) and v > 0x1000:
                    a = v
                    break
        elif isinstance(e, int):
            a = e
        if a:
            out.append(a)
    return sorted(set(out))


EXPORT_ADDRS = export_addrs()


def _vt_slots():
    slots = {}
    try:
        vts = json.load(io.open(os.path.join(RE, "vtables.json"), encoding="utf-8"))
        for _name, v in vts.items():
            rva = v.get("vtable_rva")
            s = [x for x in (v.get("slots") or []) if x in PROF]
            if rva is None or not s:
                continue
            slots.setdefault(rva, []).extend(s)
            slots.setdefault(rva + 16, []).extend(s)   # vptr points at the address point
    except Exception as e:
        print("covlib: could not load vtables.json:", e)
    return slots


VT_SLOTS = _vt_slots()


def reachable():
    """Everything the 168 exports can reach: direct callees + vtable dispatch."""
    seen, q = set(), deque()
    for a in EXPORT_ADDRS:
        if a in PROF and a not in seen:
            seen.add(a)
            q.append(a)
    while q:
        a = q.popleft()
        f = PROF.get(a, {})
        nxt = list(f.get("callees") or [])
        for d in (f.get("data_refs") or []):
            nxt.extend(VT_SLOTS.get(d, ()))
        for c in nxt:
            if c in PROF and c not in seen:
                seen.add(c)
                q.append(c)
    return seen


# Files that must NEVER count as citations: the raw data tables and anything this toolchain
# generates. Otherwise "listing a function as uncovered" would itself mark it covered.
SKIP_NAMES = {"exports_table.csv", "exports_table.json", "exports_table.md",
              "UNCOVERED_RANKED.md", "RECOVERY_STATUS.md", "TU_MAP.md", "vtables.json",
              "prof2.pkl", "g_coverage.py", "g_tu_map.py", "covlib.py", "results.csv"}
ADDR_RE = re.compile(r"0x([0-9A-Fa-f]{3,8})")


def cited_set(extra_skip=()):
    """Function entry addresses mentioned in the narrative docs / sources -> {rva: times}."""
    skip = set(SKIP_NAMES) | set(extra_skip)
    files = list(glob.glob(os.path.join(RE, "*.md"))) + list(glob.glob(os.path.join(RE, "*.py")))
    for root, _d, fs in os.walk(LC):
        if os.sep + "build" in root:
            continue
        for f in fs:
            if f.endswith((".cpp", ".hpp", ".md", ".py", ".txt", ".svg")):
                files.append(os.path.join(root, f))
    cited = Counter()
    for fp in files:
        if os.path.basename(fp) in skip:
            continue
        try:
            t = io.open(fp, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for m in ADDR_RE.finditer(t):
            v = int(m.group(1), 16)
            if v in PROF:
                cited[v] += 1
    return cited


# --- classification of un-cited reachable code, split three ways -----------------------------
# Human instruction (goal round 2): a third party library is to be DOWNLOADED AND LINKED, not
# reverse engineered, so it must be excluded from the "still to reverse" number -- but the
# exclusion has to be explicit and evidence based, which is what third_party/fetch.py's manifest is.
TOOLCHAIN_PAT = re.compile(
    r"(std::__|__gnu_cxx|libstdc\+\+|\[abi:|_M_|basic_string::|vector::_M|"
    r"terminate called|__cxa_|operator new|operator delete|std::(length|out_of)_error)", re.I)
THIRD_PARTY_PAT = re.compile(
    r"(boost_1_63_0|/boost/|cryptopp|CryptoPP|\bCrypto|sha1|sha256|\bAES\b|RSA|DSA|"
    r"\bClp\b|\bOsi\b|OsiClp|OsiSolverInterface|CoinUtils|\bCoin\b|coin-or|clpModel|"
    r"jsoncpp|json/value\.h|Json::|absl::|\bAbseil\b)", re.I)


def classify(a):
    """'toolchain' | 'third_party' | 'domain' for a reachable function address."""
    f = PROF[a]
    text = " ".join(str(s[1]) if isinstance(s, (tuple, list)) and len(s) == 2 else str(s)
                    for s in (f.get("strings") or []))
    names = str(f.get("name") or "")
    blob = text + " " + names
    if TOOLCHAIN_PAT.search(blob):
        return "toolchain"
    if THIRD_PARTY_PAT.search(blob):
        return "third_party"
    return "domain"


def hint_of(f):
    for s in (f.get("strings") or []):
        if isinstance(s, (tuple, list)) and len(s) == 2:
            return str(s[1])
        if isinstance(s, str):
            return s
    if f.get("data_refs"):
        return "data@0x%x" % f["data_refs"][0]
    return ""
