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
    if a in LIBRARY_EVIDENCED:
        return LIBRARY_EVIDENCED[a][0]
    if a in LIBSTDCXX_EVIDENCED:
        return "toolchain"
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
    r"xsize   =|CoinMessageHandler|OsiSolverInterface|number of rows|ClpSimplex|ClpModel|NAME          |OBJROW|COLUMNS|RANGES|BOUNDS|ENDATA|exmip1|p0033|flugpl|enigma|mod011|probing|mas76)",
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

# --- methodology helpers (goal round 36) -------------------------------------------------------
# Four mistakes I made in a row all had the same shape: a filter condition was written too
# loosely, so the result was systematically biased. They are encoded here so that the correct
# method is also the easy one.
#   1. field-offset scans must PIN THE BASE REGISTER -- otherwise [rsp+0x58] stack locals are
#      counted as object fields (this produced a wrong "writers of +0x58" list of 103 entries
#      where the true answer is 46).
#   2. candidate lists must be filtered by REACHABILITY first (otherwise unreachable COIN-OR code
#      looks like work in the domain bucket).
#   3. generated artefacts must never count as citations (see SKIP_NAMES).
#   4. an "owner" in an ownership table must itself HAVE identity.
_STACK_BASES = ("rsp", "rbp")

def field_writes_scan(disp, addrs=None, width=None, is_float=None):
    """Functions that write to [reg+disp] on a NON-stack base. Returns {addr: [(site, base)]}.

    ALWAYS state the query, because the same offset gives very different answers:
      width=None, is_float=None  -> anything writes there           (+0x58: 810 functions)
      width=8,    is_float=True  -> a double is written there       (+0x58:  46 functions)
    Not saying which question you asked is exactly how the wrong "writers of +0x58" list of 103
    entries was produced earlier (that one also lacked the base-register pin).
    """
    from capstone.x86 import X86_OP_MEM, X86_REG_RIP
    out = {}
    for a in (addrs if addrs is not None else PROF):
        f = PROF.get(a) or {}
        try:
            for ins in disasm(a):
                if not ins.mnemonic.startswith("mov") or ", " not in ins.op_str:
                    continue
                for o in ins.operands:
                    if o.type == X86_OP_MEM and o.mem.base != X86_REG_RIP and o.mem.disp == disp:
                        nm = ins.reg_name(o.mem.base)
                        if nm in _STACK_BASES:
                            continue
                        if width is not None or is_float is not None:
                            src = ins.op_str.split(", ", 1)[1] if ", " in ins.op_str else ""
                            fl = src.startswith("xmm")
                            if is_float is not None and fl != is_float:
                                continue
                            if width is not None:
                                w = 8 if ("qword" in ins.op_str or fl) else (
                                    4 if "dword" in ins.op_str else (
                                    2 if "word" in ins.op_str else 1))
                                if w != width:
                                    continue
                        out.setdefault(a, []).append((ins.address, nm))
        except Exception:
            pass
    return out


def reachable_uncited_domain():
    """(reachable, uncited, domain) address sets, computed the only correct way."""
    import json as _json
    vts = _json.load(io.open(os.path.join(RE, "vtables.json"), encoding="utf-8"))
    slots = {}
    for _n, v in vts.items():
        rva = v.get("vtable_rva")
        s = [x for x in (v.get("slots") or []) if x in PROF]
        if rva is None or not s:
            continue
        slots.setdefault(rva, []).extend(s)
        slots.setdefault(rva + 16, []).extend(s)

    def ea(e):
        if isinstance(e, dict):
            for k in ("address", "rva", "addr", "func", "entry"):
                if k in e and e[k]:
                    return int(e[k])
            return None
        if isinstance(e, (list, tuple)):
            for v in e:
                if isinstance(v, int) and v > 0x1000:
                    return v
            return None
        return int(e) if isinstance(e, int) else None

    from collections import deque as _dq
    seen, q = set(), _dq()
    for a in sorted({a for a in (ea(e) for e in EXPORTS) if a}):
        if a in PROF and a not in seen:
            seen.add(a); q.append(a)
    while q:
        a = q.popleft()
        f = PROF.get(a, {})
        nxt = list(f.get("callees") or [])
        for d in (f.get("data_refs") or []):
            nxt.extend(slots.get(d, ()))
        for c in nxt:
            if c in PROF and c not in seen:
                seen.add(c); q.append(c)
    cit = set(cited_set())
    unc = seen - cit
    dom = {a for a in unc if classify_identity(a) == "domain"}
    return seen, unc, dom

# --- libstdc++ routines PROVEN by reading them, one at a time (goal round 75) --------------------
# Each entry carries the evidence that made it a toolchain routine rather than domain code. Nothing
# enters this set on a guess, and the size of the set is reported together with its effect.
LIBSTDCXX_EVIDENCED = {
    0x910BA0: "the allocation helper _M_construct calls when the length exceeds 15; 1002 callers, so it is reached from string operations all over the binary (round 76)",
    0x90F310: "std::string::_M_construct: the body carries the literal assertion text 'basic_string::_M_construct null not valid', compares the length against 0xf (the 15 byte small-string capacity of a 32 byte std::string) and calls 0x910BA0 for the heap case (round 76)",
    0x867DF0: "0x8F17B0 sibling: reads the streambuf out of [+0xE8], calls vtable slot +0x30 and "
              "compares the result with -1 (traits::eof()), then sets bit 0 of the state word at "
              "+0x20 -- that is eofbit, i.e. an iostream uflow/underflow path (round 73)",
    0x8682A0: "builds the (bool, T&) result the try-to-obtain helper returns: first byte = 0 and set "
              "to 1 on success, and the failure path sets bit 2 of the same state word -- badbit in "
              "std::ios_base -- then tail calls the throw helper 0x9456A0 (round 72)",
    0x978010: "the stream extraction path those two serve, entered through 0x8682A0 and with the same "
              "+0x20 state word and vptr-0x18 virtual base adjustment (rounds 71-73)",
    0x8F17B0: "classic libstdc++ std::string move: pointer at +0, size at +8, SSO buffer at +0x10, "
              "32 byte objects, and the destination slot advanced by 0x20 with a reallocation "
              "branch at the end -- vector<string>::emplace_back from a moved string (round 74)",
}

# --- library code PROVEN by the class it references (goal round 94) -----------------------------
# The rule that produced this list, applied strictly so it cannot swallow domain code:
#   every class the function references (RTTI or vtable address point) has a library name
#   prefix, AND the function carries no strings of its own (no TU path, no assertion text).
# A function that keeps a string is left in the domain bucket, because a domain function may
# well catch a boost exception.
LIBRARY_EVIDENCED = {
    0xC03B0: ("third_party", "N8CryptoPP18PK_SignatureScheme11KeyTooShortE"),
    0xC0610: ("third_party", "N8CryptoPP18PK_SignatureScheme11KeyTooShortE"),
    0xC0CE0: ("third_party", "N8CryptoPP18PK_SignatureScheme11KeyTooShortE"),
    0x117EA0: ("third_party", "N8CryptoPP22BufferedTransformation16NoChannelSupportE"),
    0x117F40: ("third_party", "N8CryptoPP22BufferedTransformation16NoChannelSupportE"),
    0x118000: ("third_party", "N8CryptoPP22BufferedTransformation16NoChannelSupportE"),
    0x1180C0: ("third_party", "N8CryptoPP22BufferedTransformation16NoChannelSupportE"),
    0x712740: ("third_party", "N5boost8geometry19turn_info_exceptionE"),
    0x713650: ("third_party", "N5boost8geometry19turn_info_exceptionE"),
    0x77FB50: ("third_party", "N8CryptoPP14InputRejectingINS_22BufferedTransformationEE13In"),
    0x77FE00: ("third_party", "N8CryptoPP14InputRejectingINS_22BufferedTransformationEE13In"),
    0x77FE50: ("third_party", "N8CryptoPP14InputRejectingINS_22BufferedTransformationEE13In"),
    0x77FEA0: ("third_party", "N8CryptoPP14InputRejectingINS_22BufferedTransformationEE13In"),
    0x77FEF0: ("third_party", "N8CryptoPP14InputRejectingINS_6FilterEE13InputRejectedE"),
    0x7801A0: ("third_party", "N8CryptoPP14InputRejectingINS_6FilterEE13InputRejectedE"),
    0x7801F0: ("third_party", "N8CryptoPP14InputRejectingINS_6FilterEE13InputRejectedE"),
    0x780240: ("third_party", "N8CryptoPP14InputRejectingINS_6FilterEE13InputRejectedE"),
    0x786700: ("third_party", "N8CryptoPP16HashInputTooLongE"),
    0x799F60: ("third_party", "N8CryptoPP23AlgorithmParametersBase16ParameterNotUsedE"),
    0x97A7B0: ("toolchain", "NSt8ios_base7failureE"),
    0x990540: ("toolchain", "NSt6locale5facetE"),
    0x990600: ("toolchain", "NSt6locale5facetE"),
    0x990780: ("toolchain", "NSt6locale5facetE"),
    0x990840: ("toolchain", "NSt6locale5facetE"),
    0x9916E0: ("toolchain", "NSt6locale5facetE"),
    0x9917A0: ("toolchain", "NSt6locale5facetE"),
    0x991800: ("toolchain", "NSt6locale5facetE"),
    0x991920: ("toolchain", "NSt6locale5facetE"),
    0x9919E0: ("toolchain", "NSt6locale5facetE"),
}

# --- bucket C library code (goal round 110): every class it references is a library type ---
# --- bucket C, corrected rule (round 110c): all referenced classes are library types ---
LIBRARY_EVIDENCED[0xB8930] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0xBB070] = ("third_party", "CryptoPP::PK_FinalTemplate::<<subst>::TF_VerifierImpl::<")
LIBRARY_EVIDENCED[0xC1C80] = ("third_party", "CryptoPP::ByteQueue::Walker")
LIBRARY_EVIDENCED[0xC2110] = ("third_party", "CryptoPP::ByteQueue::Walker")
LIBRARY_EVIDENCED[0xC2200] = ("third_party", "CryptoPP::ByteQueue::Walker")
LIBRARY_EVIDENCED[0xC2510] = ("third_party", "CryptoPP::ByteQueue")
LIBRARY_EVIDENCED[0xC2590] = ("third_party", "CryptoPP::ByteQueue")
LIBRARY_EVIDENCED[0xC2610] = ("third_party", "CryptoPP::ByteQueue::Walker")
LIBRARY_EVIDENCED[0xC2860] = ("third_party", "CryptoPP::ByteQueue::Walker")
LIBRARY_EVIDENCED[0xC2EC0] = ("third_party", "CryptoPP::ByteQueue::Walker")
LIBRARY_EVIDENCED[0xC33F0] = ("third_party", "CryptoPP::ByteQueue")
LIBRARY_EVIDENCED[0xD2370] = ("third_party", "CryptoPP::HashFilter")
LIBRARY_EVIDENCED[0xF0E90] = ("third_party", "CryptoPP::Integer")
LIBRARY_EVIDENCED[0xF12C0] = ("third_party", "CryptoPP::Integer")
LIBRARY_EVIDENCED[0xF3AB0] = ("third_party", "CryptoPP::Integer")
LIBRARY_EVIDENCED[0xF49E0] = ("third_party", "CryptoPP::Integer")
LIBRARY_EVIDENCED[0xF4DE0] = ("third_party", "CryptoPP::Integer")
LIBRARY_EVIDENCED[0xF4EE0] = ("third_party", "CryptoPP::Integer")
LIBRARY_EVIDENCED[0xF5020] = ("third_party", "CryptoPP::Integer")
LIBRARY_EVIDENCED[0xF7260] = ("third_party", "CryptoPP::Integer")
LIBRARY_EVIDENCED[0x100180] = ("third_party", "CryptoPP::MessageQueue")
LIBRARY_EVIDENCED[0x10F200] = ("third_party", "CryptoPP::AlgorithmParameters")
LIBRARY_EVIDENCED[0x10F220] = ("third_party", "CryptoPP::AlgorithmParameters")
LIBRARY_EVIDENCED[0x10F770] = ("third_party", "CryptoPP::BERGeneralDecoder")
LIBRARY_EVIDENCED[0x10F810] = ("third_party", "CryptoPP::BERGeneralDecoder")
LIBRARY_EVIDENCED[0x10FA20] = ("third_party", "CryptoPP::DERGeneralEncoder")
LIBRARY_EVIDENCED[0x10FBB0] = ("third_party", "CryptoPP::DERGeneralEncoder")
LIBRARY_EVIDENCED[0x111630] = ("third_party", "CryptoPP::BERGeneralDecoder")
LIBRARY_EVIDENCED[0x111AD0] = ("third_party", "CryptoPP::DERGeneralEncoder")
LIBRARY_EVIDENCED[0x1186C0] = ("third_party", "CryptoPP::BitBucket")
LIBRARY_EVIDENCED[0x1187C0] = ("third_party", "CryptoPP::BitBucket")
LIBRARY_EVIDENCED[0x1188A0] = ("third_party", "CryptoPP::BitBucket")
LIBRARY_EVIDENCED[0x119110] = ("third_party", "CryptoPP::BitBucket")
LIBRARY_EVIDENCED[0x11A780] = ("third_party", "CryptoPP::BitBucket")
LIBRARY_EVIDENCED[0x6019E0] = ("third_party", "Json::StyledWriter")
LIBRARY_EVIDENCED[0x60B4E0] = ("toolchain", "dbg::symlog")
LIBRARY_EVIDENCED[0x65C5C0] = ("toolchain", "N9__gnu_cxx26__concurrence_unlock_errorE")
LIBRARY_EVIDENCED[0x65C700] = ("toolchain", "N9__gnu_cxx26__concurrence_unlock_errorE")
LIBRARY_EVIDENCED[0x679220] = ("toolchain", "dbg::file_error")
LIBRARY_EVIDENCED[0x681A30] = ("third_party", "Json::StyledWriter")
LIBRARY_EVIDENCED[0x6DB910] = ("third_party", "boost::asio::basic_streambuf::<>")
LIBRARY_EVIDENCED[0x6DD270] = ("third_party", "boost::asio::basic_streambuf::<>")
LIBRARY_EVIDENCED[0x6DE2B0] = ("third_party", "boost::detail::sp_counted_impl_p::<<subst>::filesystem::")
LIBRARY_EVIDENCED[0x6DE430] = ("third_party", "boost::detail::sp_counted_impl_p::<<subst>::filesystem::")
LIBRARY_EVIDENCED[0x6DE750] = ("third_party", "boost::filesystem::filesystem_error")
LIBRARY_EVIDENCED[0x6DE7E0] = ("third_party", "boost::filesystem::filesystem_error")
LIBRARY_EVIDENCED[0x6DE860] = ("third_party", "boost::bad_rational")
LIBRARY_EVIDENCED[0x6DE890] = ("third_party", "boost::bad_rational")
LIBRARY_EVIDENCED[0x6E8450] = ("third_party", "N5boost16exception_detail10clone_implINS0_19error_info_i")
LIBRARY_EVIDENCED[0x6E8600] = ("third_party", "N5boost16exception_detail10clone_implINS0_19error_info_i")
LIBRARY_EVIDENCED[0x6E8960] = ("third_party", "N5boost16exception_detail10clone_implINS0_19error_info_i")
LIBRARY_EVIDENCED[0x6E8B00] = ("third_party", "N5boost16exception_detail10clone_implINS0_19error_info_i")
LIBRARY_EVIDENCED[0x6E8E90] = ("third_party", "N5boost16exception_detail10clone_implINS0_19error_info_i")
LIBRARY_EVIDENCED[0x6E9050] = ("third_party", "N5boost16exception_detail10clone_implINS0_19error_info_i")
LIBRARY_EVIDENCED[0x6E93B0] = ("third_party", "boost::bad_rational")
LIBRARY_EVIDENCED[0x6E9410] = ("third_party", "boost::bad_rational")
LIBRARY_EVIDENCED[0x6E95C0] = ("third_party", "boost::exception_detail::clone_impl::<<subst>::error_inf")
LIBRARY_EVIDENCED[0x6E9600] = ("third_party", "boost::exception_detail::clone_impl::<<subst>::error_inf")
LIBRARY_EVIDENCED[0x6E9630] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E9680] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E96D0] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E9720] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E9810] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E9860] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E98B0] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E9900] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E99F0] = ("third_party", "boost::exception_detail::error_info_injector::<<subst>::")
LIBRARY_EVIDENCED[0x6E9B40] = ("third_party", "boost::exception_detail::error_info_injector::<>")
LIBRARY_EVIDENCED[0x6E9BB0] = ("third_party", "boost::bad_rational")
LIBRARY_EVIDENCED[0x6E9C30] = ("third_party", "boost::bad_rational")
LIBRARY_EVIDENCED[0x6E9C80] = ("third_party", "boost::bad_rational")
LIBRARY_EVIDENCED[0x6E9E30] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E9E90] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E9F10] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E9F60] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E9FA0] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6E9FF0] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6EA140] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6EA1B0] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6EA200] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6EA240] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6EA2C0] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6EA310] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x6EBA90] = ("third_party", "boost::asio::basic_streambuf::<>")
LIBRARY_EVIDENCED[0x6EBB90] = ("third_party", "boost::asio::basic_streambuf::<>")
LIBRARY_EVIDENCED[0x6EBBE0] = ("third_party", "boost::asio::basic_streambuf::<>")
LIBRARY_EVIDENCED[0x6EC6B0] = ("third_party", "boost::asio::detail::timer_queue::<<subst>::chrono_time_")
LIBRARY_EVIDENCED[0x6EC760] = ("third_party", "boost::asio::detail::timer_queue::<<subst>::chrono_time_")
LIBRARY_EVIDENCED[0x6ECEE0] = ("third_party", "boost::asio::datagram_socket_service::<<subst>::ip::udp>")
LIBRARY_EVIDENCED[0x6ECF10] = ("third_party", "boost::asio::datagram_socket_service::<<subst>::ip::udp>")
LIBRARY_EVIDENCED[0x6F0B40] = ("third_party", "boost::asio::detail::timer_queue::<<subst>::chrono_time_")
LIBRARY_EVIDENCED[0x6F0B70] = ("third_party", "boost::asio::detail::timer_queue::<<subst>::chrono_time_")
LIBRARY_EVIDENCED[0x6F4D10] = ("third_party", "boost::asio::detail::win_iocp_io_service")
LIBRARY_EVIDENCED[0x6F4D80] = ("third_party", "boost::asio::detail::win_iocp_io_service")
LIBRARY_EVIDENCED[0x6FDFE0] = ("third_party", "boost::system::system_error")
LIBRARY_EVIDENCED[0x6FE020] = ("third_party", "boost::system::system_error")
LIBRARY_EVIDENCED[0x701270] = ("third_party", "boost::geometry::exception")
LIBRARY_EVIDENCED[0x7012A0] = ("third_party", "boost::geometry::exception")
LIBRARY_EVIDENCED[0x701F70] = ("third_party", "boost::geometry::exception")
LIBRARY_EVIDENCED[0x701FC0] = ("third_party", "boost::geometry::exception")
LIBRARY_EVIDENCED[0x704370] = ("third_party", "boost::geometry::exception")
LIBRARY_EVIDENCED[0x7043A0] = ("third_party", "boost::geometry::exception")
LIBRARY_EVIDENCED[0x7080C0] = ("third_party", "boost::geometry::exception")
LIBRARY_EVIDENCED[0x7080F0] = ("third_party", "boost::geometry::exception")
LIBRARY_EVIDENCED[0x71B540] = ("third_party", "N5boost8geometry31overlay_invalid_input_exceptionE")
LIBRARY_EVIDENCED[0x74B970] = ("third_party", "boost::geometry::exception")
LIBRARY_EVIDENCED[0x74B9A0] = ("third_party", "boost::geometry::exception")
LIBRARY_EVIDENCED[0x7781F0] = ("third_party", "CryptoPP::HashFilter")
LIBRARY_EVIDENCED[0x77AC60] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x77ACA0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x77C350] = ("third_party", "CryptoPP::MessageQueue")
LIBRARY_EVIDENCED[0x77C410] = ("third_party", "CryptoPP::MessageQueue")
LIBRARY_EVIDENCED[0x77EDB0] = ("third_party", "CryptoPP::TF_ObjectImpl::<<subst>::TF_VerifierBase>::<su")
LIBRARY_EVIDENCED[0x77EE90] = ("third_party", "CryptoPP::TF_ObjectImpl::<<subst>::TF_VerifierBase>::<su")
LIBRARY_EVIDENCED[0x77FBA0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x77FD70] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x77FDB0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x77FF40] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x780110] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x780150] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x780850] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x780890] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x780980] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x7809C0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x7822B0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x7822F0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x782630] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x782670] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x785D60] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x785DA0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x78A870] = ("third_party", "CryptoPP::TF_ObjectImpl::<<subst>::TF_VerifierBase>::<su")
LIBRARY_EVIDENCED[0x78A950] = ("third_party", "CryptoPP::TF_ObjectImpl::<<subst>::TF_VerifierBase>::<su")
LIBRARY_EVIDENCED[0x78D7B0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x78D7F0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x78F380] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x78F540] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x78F580] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x78F5C0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x78F600] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x78FB10] = ("third_party", "CryptoPP::AlgorithmParameters")
LIBRARY_EVIDENCED[0x78FB40] = ("third_party", "CryptoPP::AlgorithmParameters")
LIBRARY_EVIDENCED[0x7982B0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x7982F0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x799EE0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x799F20] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x79CC80] = ("third_party", "CryptoPP::IteratedHashWithStaticTransform::<<subst>::Enu")
LIBRARY_EVIDENCED[0x79CDF0] = ("third_party", "CryptoPP::IteratedHashWithStaticTransform::<<subst>::Enu")
LIBRARY_EVIDENCED[0x7A2B00] = ("third_party", "CryptoPP::IteratedHashWithStaticTransform::<<subst>::Enu")
LIBRARY_EVIDENCED[0x7A2B70] = ("third_party", "CryptoPP::IteratedHashWithStaticTransform::<<subst>::Enu")
LIBRARY_EVIDENCED[0x7ACF30] = ("third_party", "CryptoPP::IteratedHashWithStaticTransform::<<subst>::Enu")
LIBRARY_EVIDENCED[0x7ACFA0] = ("third_party", "CryptoPP::IteratedHashWithStaticTransform::<<subst>::Enu")
LIBRARY_EVIDENCED[0x7B0490] = ("third_party", "CryptoPP::Integer")
LIBRARY_EVIDENCED[0x7B04D0] = ("third_party", "CryptoPP::Integer")
LIBRARY_EVIDENCED[0x7B1F20] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x7B1F70] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x7B2060] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x7B20A0] = ("third_party", "CryptoPP::Exception")
LIBRARY_EVIDENCED[0x7C4660] = ("toolchain", "__gnu_cxx::__concurrence_lock_error")
LIBRARY_EVIDENCED[0x7C4690] = ("toolchain", "__gnu_cxx::__concurrence_lock_error")
LIBRARY_EVIDENCED[0x7C46A0] = ("toolchain", "__gnu_cxx::__concurrence_wait_error")
LIBRARY_EVIDENCED[0x7C46D0] = ("toolchain", "__gnu_cxx::__concurrence_wait_error")
LIBRARY_EVIDENCED[0x7C46E0] = ("toolchain", "__gnu_cxx::__concurrence_unlock_error")
LIBRARY_EVIDENCED[0x7C4710] = ("toolchain", "__gnu_cxx::__concurrence_unlock_error")
LIBRARY_EVIDENCED[0x7C4A40] = ("toolchain", "__gnu_cxx::__concurrence_broadcast_error")
LIBRARY_EVIDENCED[0x7C4A70] = ("toolchain", "__gnu_cxx::__concurrence_broadcast_error")
LIBRARY_EVIDENCED[0x7C4A80] = ("toolchain", "N9__gnu_cxx24__concurrence_lock_errorE")
LIBRARY_EVIDENCED[0x7C4AB0] = ("toolchain", "N9__gnu_cxx29__concurrence_broadcast_errorE")
LIBRARY_EVIDENCED[0x7D9A70] = ("third_party", "boost::bad_rational")
LIBRARY_EVIDENCED[0x7D9C20] = ("third_party", "N5boost16exception_detail10clone_implINS0_19error_info_i")
LIBRARY_EVIDENCED[0x7DA180] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x7DA290] = ("third_party", "N5boost16exception_detail10clone_implINS0_19error_info_i")
LIBRARY_EVIDENCED[0x7DA380] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x7DA530] = ("third_party", "N5boost16exception_detail10clone_implINS0_19error_info_i")
LIBRARY_EVIDENCED[0x7DA5B0] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x7DA680] = ("third_party", "N5boost16exception_detail10clone_implINS0_19error_info_i")
LIBRARY_EVIDENCED[0x7DA970] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x7DAB10] = ("third_party", "N5boost16exception_detail10clone_implINS0_19error_info_i")
LIBRARY_EVIDENCED[0x7DAB90] = ("third_party", "boost::exception")
LIBRARY_EVIDENCED[0x7DAD40] = ("third_party", "N5boost16exception_detail10clone_implINS0_19error_info_i")
LIBRARY_EVIDENCED[0x7F56C0] = ("third_party", "CryptoPP::IteratedHashWithStaticTransform::<<subst>::Enu")
LIBRARY_EVIDENCED[0x809F30] = ("third_party", "CryptoPP::IteratedHashWithStaticTransform::<<subst>::Enu")
LIBRARY_EVIDENCED[0x81C080] = ("third_party", "CryptoPP::PSSR_MEM::<<subst>::P1363_MGF1>::E::")
LIBRARY_EVIDENCED[0x998CD0] = ("toolchain", "N9__gnu_cxx26__concurrence_unlock_errorE")
LIBRARY_EVIDENCED[0x99FE70] = ("third_party", "N5boost8geometry18centroid_exceptionE")
LIBRARY_EVIDENCED[0x9A0700] = ("toolchain", "N9__gnu_cxx26__concurrence_unlock_errorE")
