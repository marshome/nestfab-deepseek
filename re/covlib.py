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
SKIP_NAMES = {
              # Generated inventories and the tooling that writes them. They list thousands
              # of addresses that carry no identity (re/IDENTIFIED.md is 80% 'shape only'),
              # so counting them as 'cited' would inflate every number -- which is exactly
              # what happened to re/TU_MAP.md before this fix (90.3% 'cited' for the own TUs).
              # g_coverage.py already applied this rule; now the TU tooling inherits it too.
              "IDENTIFIED.md", "identified_summary.json", "g_identify.py",
              "VTABLE_SLOTS.md", "vtable_slots_summary.json", "g_vtable_slots.py",
              "STRATEGY_METHODS.md", "g_strategy_methods.py",
              # same rule for the shape-level sweep: it is tier C by construction
              "SWEEP.md", "g_sweep.py","exports_table.csv", "exports_table.json", "exports_table.md",
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
    r"(boost_1_63_0|/boost/|boost::|asio::|cryptopp|CryptoPP|\bCrypto|sha1|sha256|\bAES\b|RSA|DSA|"
    r"\bClp\b|\bOsi\b|OsiClp|OsiSolverInterface|CoinUtils|\bCoin\b|Coin::|coin-or|clpModel|"
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


# --- identity-based classification (goal round 7) ---------------------------------------------
# The rule above excludes a function as soon as ANY string it references matches. But the strings a
# function references include the names of the functions it CALLS, so a domain function that merely
# calls std::vector::reserve was being moved out of the "still to reverse" list. Measured on the
# current data: 64 functions / 125,925 bytes were excluded that way alone. That is an optimistic
# bias -- it hides work -- so the exclusion now requires IDENTITY evidence:
#
#   * the function's own recovered NAME is a library symbol, or
#   * ALL of its strings are library symbols (nothing domain specific at all), or
#   * its strings show it was compiled from a third party SOURCE PATH (boost/, cryptopp/, clp/,
#     osi/, coinutils/, jsoncpp/ under external/ or third_party/),
#
# and a called-library string alone is no longer enough.
VENDOR_PATH_PAT = re.compile(
    r"(external[\\/](boost_1_63_0|clp|coinutils|osi|cryptopp|jsoncpp)|"
    r"third_party[\\/]src[\\/](boost_1_63_0|clp-|coinutils-|osi-|cryptopp|jsoncpp)|"
    r"(^|[\\/])boost[\\/][a-z0-9_]+\.hpp|"
    r"cryptopp[\\/]|jsoncpp[\\/]|coin-or)", re.I)


def classify_identity(a):
    """Same three names as classify(), but only on identity evidence (see the note above)."""
    f = PROF[a]
    strs = []
    for s in (f.get("strings") or []):
        strs.append(str(s[1]) if isinstance(s, (tuple, list)) and len(s) == 2 else str(s))
    strs = [s for s in strs if s]
    name = str(f.get("name") or "")
    if TOOLCHAIN_PAT.search(name):
        return "toolchain"
    if THIRD_PARTY_PAT.search(name):
        return "third_party"
    # the class that owns this vtable slot, when there is one, is identity evidence too
    cls = slot_class_of(a)
    if cls:
        if THIRD_PARTY_PAT.search(cls):
            return "third_party"
        if TOOLCHAIN_PAT.search(cls) or cls.startswith("std::"):
            return "toolchain"
    if any(VENDOR_PATH_PAT.search(s) for s in strs):
        return "third_party"
    if is_coin_internal(a):
        return "third_party"
    if strs:
        lib = [s for s in strs if TOOLCHAIN_PAT.search(s) or THIRD_PARTY_PAT.search(s)]
        if len(lib) == len(strs):
            return "toolchain" if not any(THIRD_PARTY_PAT.search(s) for s in strs) else "third_party"
    return "domain"


# --- COIN-OR internals recognised by their own message text (goal round 38) --------------------
# The biggest un-cited "domain" functions turned out to be Clp / CoinUtils / Osi internals whose
# strings are their own log and assertion messages -- 'Presolve', 'CoinPresolve initial state',
# 'bad fscanf', 'scalingFlag_', 'maxDelta < tolerance', 'Objective offset is', 'Time to decompose'.
# None of those contain the word Clp, so the earlier patterns missed them and megabytes of third
# party code sat in the "still to reverse" bucket. Per the human instruction a third party library
# is downloaded and linked, NOT reversed, so this evidence excludes them -- and it is evidence, not
# a guess: these are verbatim COIN-OR log strings.
CLP_INTERNAL_PAT = re.compile(
    r"(Presolve|CoinPresolve|presolve|bad fscanf|scalingFlag|maxDelta|Objective offset is|"
    r"Time to decompose|dual infeasible|saying infeasible|small drop|lastobj|fixing %d|"
    r"empty rows and|CoinLpIO|CoinMpsIO|CoinPackedMatrix|row_%d|theta %g|"
    r"xsize   =|CoinMessageHandler|OsiSolverInterface|number of rows|ClpSimplex|ClpModel)",
    re.I)


def is_coin_internal(a):
    """True when the function's own strings are COIN-OR log/assertion text."""
    f = PROF[a]
    strs = []
    for s in (f.get("strings") or []):
        strs.append(str(s[1]) if isinstance(s, (tuple, list)) and len(s) == 2 else str(s))
    return any(CLP_INTERNAL_PAT.search(s) for s in strs if s)


def has_identity_evidence(a):
    """True when there is anything at all to identify the function by (name, string, data ref)."""
    f = PROF[a]
    if f.get("name"):
        return True
    if f.get("strings"):
        return True
    return False


# --- vtable CLASS ownership as identity evidence (goal round 9) --------------------------------
# Round 9 measured that of the 595 un-cited domain functions that are slots of a known vtable, most
# are members of THIRD PARTY classes -- CryptoPP::HexEncoder (43), CryptoPP::PSSR_MEM (15),
# CryptoPP::DERGeneralEncoder (14), boost::asio::ip::resolver_service<udp> (4) and so on. Only a
# minority are domain classes (Pack::RecursiveNester, Multi::*, Tiling::*). A function that occupies
# slot k of CryptoPP::HexEncoder IS CryptoPP code, so the class name is identity evidence and those
# functions must not sit in the "domain still to reverse" bucket. (This is the mirror image of the
# round 7 fix: there the rule was too eager to exclude, here it was too eager to include. Both
# directions are now driven by evidence rather than by a called function's name.)
_SLOT_CLASS = None


def slot_class_of(a):
    """Class name owning the vtable slot at `a`, or None."""
    global _SLOT_CLASS
    if _SLOT_CLASS is None:
        _SLOT_CLASS = {}
        try:
            import json as _json
            p = r"D:\Nesting\nestfab\re\vtables.json"
            vts = _json.load(io.open(p, encoding="utf-8"))
            for cls, v in vts.items():
                nm = v.get("demangled") or cls
                for s in (v.get("slots") or []):
                    if s:
                        _SLOT_CLASS.setdefault(s, nm)
        except Exception:
            pass
    return _SLOT_CLASS.get(a)


def hint_of(f):
    for s in (f.get("strings") or []):
        if isinstance(s, (tuple, list)) and len(s) == 2:
            return str(s[1])
        if isinstance(s, str):
            return s
    if f.get("data_refs"):
        return "data@0x%x" % f["data_refs"][0]
    return ""
