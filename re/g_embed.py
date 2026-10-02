# -*- coding: utf-8 -*-
"""Generate the embedded-original-code artifacts from libcns_dump_64.dll.

Why this exists (round 355, on the user's instruction): for domain code that has NOT been reimplemented, the project must
still carry the original bytes, embedded in the C++ -- either as an executable function (so a differential test can call
it) or as a byte array plus the disassembly as a comment, with the reason it cannot be called.

How a block is classified, mechanically, never by opinion:
  * callable      -- no RIP-relative memory operand, no call/jmp whose target lies outside the block, no absolute
                     address inside the image. Such a block is position-independent and executes correctly wherever it
                     is placed, so the test can call it.
  * comment_only  -- one of those appears; the reason string names the first few. The bytes are still embedded as data,
                     and the disassembly is emitted as comments, but the project does not pretend it can run it.

Outputs
  lcns/src/embedded/gen_orig.S        executable copies of the callable blocks + a pointer table
  lcns/src/embedded/gen_blobs.cpp     byte arrays for EVERY block + the metadata table (generated C++)
  re/embedded_registry.json           the registry, as the verifier's source of truth
  re/EMBEDDED.md                      the human-readable registry, with a disassembly listing per block
"""
import hashlib
import io
import json
import os
import struct
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *          # noqa: E402
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP  # noqa: E402

ROOT = r"D:\Nesting\nestfab"
LC = os.path.join(ROOT, "lcns")
RE = os.path.join(ROOT, "re")
OUT_S = os.path.join(LC, r"src\embedded\gen_orig.S")
OUT_CPP = os.path.join(LC, r"src\embedded\gen_blobs.cpp")
OUT_JSON = os.path.join(RE, "embedded_registry.json")
OUT_MD = os.path.join(RE, "EMBEDDED.md")
IMAGE_BASE = 0x6B4C0000
IMAGE_SIZE = 0xB43000
LISTING_LIMIT = 1024          # blocks larger than this get their listing in the markdown only

# (rva, size, note) -- the functions this session has actually read. Sizes are the profile's.
BLOCKS = [
    (0x51D2F0, None, "pointer getter: returns [rcx+0x60]"),
    (0x4F8370, None, "double accessor: returns [rcx+0x28]"),
    (0x4F8380, None, "double accessor: returns [rcx+0x30]"),
    (0x4DDD10, None, "returns the address of the field at +0x48"),
    (0x16C270, None, "packed double addition of two 2D points (addpd)"),
    (0x24B440, None, "two-dimensional cross product / orientation determinant"),
    (0x5CFD80, None, "in-place 2x3 affine transform of one point"),
    (0x5CFDC0, None, "in-place 2x3 affine transform of both points of a segment"),
    (0x5CEA80, None, "affine transform applied to a source record, functional form"),
    (0x5CF6B0, None, "affine transform, out of place"),
    (0x5CE970, None, "composition of two 2x3 affine transforms"),
    (0x5CE7B0, None, "builds a translation matrix (identity basis + point)"),
    (0x5CED50, None, "inverse of a 2x3 affine matrix"),
    (0x55E190, None, "segment length pair, min and max, with a square-root guard"),
    (0x62FE20, None,
     "libm sqrt: the C library square root, identified in round 356 from its own error path (the name string \"sqrt\" at "
     "rva 0xA06820, EDOM=0x21 stored through the errno helper 0x63F4D8, then an __math_invalid-shaped call). Its 89 "
     "callers are geometry code taking lengths; round 340 read it as a classification guard, which this corrects"),
    (0x62FE00, None, "packed sibling of the guard"),
    (0x50FD40, None, "accumulator over a range of 312-byte elements"),
    (0x5C8C50, None,
     "merge two min/max boxes: if the source's flag byte is non-zero nothing happens, if the destination's is non-zero it is "
     "re-initialised from the source, otherwise the four doubles are min/max combined. 62 instructions, no calls, 56 "
     "callers -- the same box layout as 0x5C8A10, and a common step behind GetLength/GetHeight"),
    (0x524EE0, None,
     "the subsystem behind GetLength's loop: 1054 bytes, 241 instructions, 12 calls and a RIP-relative table at "
     "0x5FDE74. Read in round 376; embedded so the assembly is in the project while it stays unimplemented"),
    (0x4F9200, None,
     "lazily initialised object: checks the byte at +0x100 and returns [rcx+0x108] when it is set, else constructs. 434 "
     "bytes, 97 instructions, 21 callers"),
    (0x5CD800, None,
     "container construction that itself merges boxes through 0x5C8C50: 610 bytes, 145 instructions, 112 callers"),
    (0x5C8A10, None,
     "the box accumulator it calls: init-or-extend a min/max box with one pair (flag at +0x00, then minX +0x08, minY "
     "+0x10, maxX +0x18, maxY +0x20); the flag means UNINITIALISED when non-zero, which is why the caller sets it to 1 "
     "before the loop and the first call clears it"),
    (0x24DD40, None, "composition of two transformed fields with weights"),
    (0x4B81D0, None, "builds the object whose first member is the 0.01 tolerance"),
    (0x24C610, None, "four-stage geometry chain over the packed +0x70 point"),
    (0x111AD0, None, "constructor of the twins' object (two vtables)"),
    (0x243820, None, "head of the largest routine here (15,524 bytes): geometry entry"),
]

# (rva, size, note) -- read-only data whose bytes are themselves evidence, embedded so the claim travels with the code.
DATA_BLOCKS = [
    (0xA06820, 0x20,
     "libm sqrt's constant cluster: the name string \"sqrt\" then -0.0, +inf and 1.0 -- the evidence that 0x62FE20 is "
     "the C library's square root and therefore toolchain, not domain code"),
]

# External call targets that a relocated copy may point at instead, and the stub's symbol. A stub is a C++ function the
# project provides with the same ABI; the generated assembly jumps to it. Only targets whose behaviour is understood are
# listed here, so a relocation can never quietly invent a callee.
CALL_STUBS = {
    0x62FE20: ("lcns_stub_sqrt", "lcns_sqrt_shim",
               "libm sqrt, identified in round 356; the project supplies std::sqrt under the same ABI"),
}

# Every exported function, read from the export table so the embedded set follows the export list rather than a copy of
# it. These are the DLL's public surface: the ones whose behaviour has been recovered in C++ still have their bytes here,
# because that is what the differential tests compare against.
_EXPORTS_TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports_table.json")
if os.path.exists(_EXPORTS_TABLE):
    for _e in json.load(io.open(_EXPORTS_TABLE, encoding="utf-8")):
        _nm = _e.get("name") or ("sub_%05X" % _e["rva"])
        BLOCKS.append((_e["rva"], None, "export %s (ordinals %s)" % (_nm, ",".join(str(o) for o in _e.get("ords", [])))))

P = load_prof()


def classify(fn, size, callable_addresses=None):
    """Return (status, reason, relocations) from the instructions alone.

    callable_addresses is the set of addresses whose executable copies already exist (or will exist) in gen_orig.S, so a
    call to one of them can be relocated to its symbol. Anything else must be a stub in CALL_STUBS.
    """
    reasons = []
    relocations = []
    end = fn + size
    known = callable_addresses or set()
    for ins in disasm(fn):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = (ins.address + ins.size + op.mem.disp) & 0xFFFFFFFFFFFFFFFF
                if ins.mnemonic in ("call", "jmp"):
                    reasons.append("rip-relative %s to rva 0x%X" % (ins.mnemonic, t))
                else:
                    # A read of read-only data: relocation rewrites the 32-bit displacement, so the copy reads a copy of
                    # the datum. The operand's own width is what has to be copied.
                    relocations.append((ins.address, t, "data", "lcns_data_%x" % t, op.size))
            elif op.type == X86_OP_IMM and ins.mnemonic in ("call", "jmp"):
                if not (fn <= op.imm < end):
                    if ins.mnemonic == "call" and op.imm in CALL_STUBS:
                        relocations.append((ins.address, op.imm, "stub", CALL_STUBS[op.imm][0], 4))
                    elif ins.mnemonic == "call" and op.imm in known:
                        relocations.append((ins.address, op.imm, "block", "lcns_orig_%x" % op.imm, 4))
                    else:
                        reasons.append("%s to 0x%X outside the block" % (ins.mnemonic, op.imm))
            elif op.type == X86_OP_IMM and ins.mnemonic not in ("call", "jmp"):
                v = op.imm & 0xFFFFFFFFFFFFFFFF
                if IMAGE_BASE <= v < IMAGE_BASE + IMAGE_SIZE:
                    reasons.append("absolute image address 0x%X" % v)
    if reasons:
        uniq = sorted(set(reasons))
        return ("comment_only",
                "; ".join(uniq[:4]) + (" (+%d more)" % (len(uniq) - 4) if len(uniq) > 4 else ""),
                [])
    if relocations:
        return ("callable_relocated",
                "; ".join("%s at 0x%x -> %s" % (kind, at, sym) for at, _t, kind, sym, _w in relocations),
                relocations)
    return "callable", "", []


def bytes_of(fn, size):
    off = rva2off(fn)
    return bytes(data[off:off + size])


def listing_of(fn, size):
    out = []
    for ins in disasm(fn):
        if ins.address >= fn + size:
            break
        out.append("%08x  %s %s" % (ins.address, ins.mnemonic, ins.op_str))
    return out


# First pass: which addresses will have an executable copy? A plain callable block, or a relocated one.
_planned = set()
for fn, _sz, _note in BLOCKS:
    _g = P.get(fn) or {}
    _size = _g.get("size")
    if not _size:
        continue
    _status, _reason, _rel = classify(fn, _size, _planned)
    if _status in ("callable", "callable_relocated"):
        _planned.add(fn)

rows = []
for fn, _sz, note in BLOCKS:
    g = P.get(fn) or {}
    size = g.get("size")
    if not size:
        print("SKIP 0x%x: the profile has no size" % fn)
        continue
    b = bytes_of(fn, size)
    if len(b) != size:
        print("SKIP 0x%x: only %d of %d bytes are inside the image" % (fn, len(b), size))
        continue
    status, reason, relocations = classify(fn, size, _planned)
    last = list(disasm(fn))
    covered = (last[-1].address + last[-1].size) if last else fn
    rows.append({
        "rva": fn,
        "size": size,
        "bytes": b,
        "symbol": "lcns_orig_%x" % fn,
        "status": status,
        "reason": reason,
        "note": note,
        "relocations": [{"at": at, "target": tgt, "kind": kind, "symbol": sym, "width": width}
                        for at, tgt, kind, sym, width in relocations],
        "callers": len([c for c in (g.get("callers") or []) if c != fn]),
        "sha256": hashlib.sha256(b).hexdigest(),
        "listing": listing_of(fn, size),
        "covered": covered,
    })

for fn, size, note in DATA_BLOCKS:
    b = bytes_of(fn, size)
    if len(b) != size:
        print("SKIP data 0x%x: only %d of %d bytes are inside the image" % (fn, len(b), size))
        continue
    rows.append({
        "rva": fn,
        "size": size,
        "bytes": b,
        "symbol": "",
        "status": "data",
        "reason": "",
        "note": note,
        "relocations": [],
        "callers": 0,
        "sha256": hashlib.sha256(b).hexdigest(),
        "listing": [],
        "covered": fn + size,
    })

callable_rows = [r for r in rows if r["status"] in ("callable", "callable_relocated")]

# ---------------------------------------------------------------- gen_orig.S
s = []
s.append("/* generated by re/g_embed.py -- do not edit by hand.")
s.append(" *")
s.append(" * Executable copies of the original bytes of the callable blocks, plus a table of their addresses.")
s.append(" * A block is callable only when the classifier found no RIP-relative memory operand, no call or jump leaving")
s.append(" * the block and no absolute image address in it, which is what makes the copy position-independent.")
s.append(" */")
s.append("    .text")
for r in callable_rows:
    s.append("")
    s.append("/* %s  rva 0x%x, %d bytes, %d callers" % (r["note"], r["rva"], r["size"], r["callers"]))
    s.append(" * sha256 %s" % r["sha256"])
    for line in (r["listing"] if r["size"] <= LISTING_LIMIT else ["listing omitted here: see re/EMBEDDED.md"]):
        s.append(" *   " + line)
    s.append(" */")
    s.append("    .p2align 4")
    s.append("    .globl %s" % r["symbol"])
    s.append("%s:" % r["symbol"])
    # The original bytes, except where a relocation lands: a call is written symbolically, and a data read keeps its
    # opcode bytes but has its 32-bit displacement written as an expression the assembler resolves.
    by_offset = {}
    for p in r.get("relocations", []):
        by_offset[p["at"] - r["rva"]] = p
    emitted = 0
    for ins in disasm(r["rva"]):
        if ins.address >= r["rva"] + r["size"]:
            break
        start = ins.address - r["rva"]
        if start > emitted:                      # any bytes between instructions (padding) are copied verbatim
            gap = r["bytes"][emitted:start]
            s.append("    .byte " + ", ".join("0x%02x" % c for c in gap))
            emitted = start
        p = by_offset.get(start)
        if p is not None and p["kind"] == "stub" or (p is not None and p["kind"] == "block"):
            s.append("    call %s   /* was 0x%x */" % (p["symbol"], p["target"]))
        elif p is not None and p["kind"] == "data":
            head = r["bytes"][start:start + ins.size - 4]
            s.append("    .byte " + ", ".join("0x%02x" % c for c in head) + "   /* %s %s */" % (ins.mnemonic, ins.op_str))
            s.append("    .long %s - . - 4   /* was rva 0x%x */" % (p["symbol"], p["target"]))
        else:
            body = r["bytes"][start:start + ins.size]
            s.append("    .byte " + ", ".join("0x%02x" % c for c in body))
        emitted = start + ins.size
    if emitted < len(r["bytes"]):
        s.append("    .byte " + ", ".join("0x%02x" % c for c in r["bytes"][emitted:]))
    s.append("    /* end %s */" % r["symbol"])
s.append("")
# The data every relocated read needs, copied verbatim from the image and labelled by its rva. Widest use wins: a
# sixteen-byte read covers an eight-byte one at the same address.
_needed = {}
for r in callable_rows:
    for p in r.get("relocations", []):
        if p["kind"] == "data":
            _needed[p["target"]] = max(_needed.get(p["target"], 0), p["width"] or 8)
if _needed:
    s.append("")
    s.append("/* read-only data the relocated copies read, copied from the image at the address the original used */")
    for tgt in sorted(_needed):
        width = _needed[tgt]
        off = rva2off(tgt)
        body = data[off:off + width] if off is not None else b""
        if len(body) != width:
            raise SystemExit("data relocation 0x%X: only %d of %d bytes are inside the image" % (tgt, len(body), width))
        s.append("    .p2align 3")
        s.append("    .globl lcns_data_%x" % tgt)
        s.append("lcns_data_%x:   /* %d bytes at rva 0x%X */" % (tgt, width, tgt))
        s.append("    .byte " + ", ".join("0x%02x" % c for c in body))

for sym, shim, why in [CALL_STUBS[k] for k in sorted(CALL_STUBS)]:
    s.append("")
    s.append("/* %s: %s" % (sym, why))
    s.append(" * A relocated copy calls this instead of the original target; it jumps to a C++ function with the same ABI,")
    s.append(" * so what runs is the project's own behaviour.")
    s.append(" */")
    s.append("    .p2align 4")
    s.append("    .globl %s" % sym)
    s.append("%s:" % sym)
    s.append("    jmp %s" % shim)

s.append("")
s.append("/* the addresses, in the registry's callable order */")
s.append("    .data")
s.append("    .p2align 3")
s.append("    .globl lcns_orig_table")
s.append("lcns_orig_table:")
for r in callable_rows:
    s.append("    .quad %s" % r["symbol"])
s.append("")
io.open(OUT_S, "w", encoding="utf-8", newline="\n").write("\n".join(s) + "\n")

# ------------------------------------------------------------ gen_blobs.cpp
c = []
c.append("// generated by re/g_embed.py -- do not edit by hand.")
c.append("//")
c.append("// Every block this session read, with its original bytes kept in the project. Callable blocks additionally have")
c.append("// an executable copy in gen_orig.S; the rest carry the reason they cannot be called, so the gap is visible in")
c.append("// the code rather than only in a document.")
c.append('#include "lcns/embedded.hpp"')
c.append("")
c.append("namespace lcns {")
c.append("namespace embedded {")
c.append("")
for r in rows:
    c.append("// 0x%x  %d bytes  %s" % (r["rva"], r["size"], r["note"]))
    c.append("// status: %s%s" % (r["status"], ("  -- " + r["reason"]) if r["reason"] else ""))
    c.append("// sha256: %s" % r["sha256"])
    c.append("alignas(16) const unsigned char kBytes_%x[%d] = {" % (r["rva"], r["size"]))
    for i in range(0, len(r["bytes"]), 12):
        chunk = r["bytes"][i:i + 12]
        c.append("    " + " ".join("0x%02x," % x for x in chunk))
    c.append("};")
    c.append("")
c.append("const Block kBlocks[] = {")
for r in rows:
    c.append('    {0x%xu, %du, "%s", Status::%s, "%s", "%s", kBytes_%x, "%s"},'
             % (r["rva"], r["size"], r["symbol"],
                {"callable": "Callable", "callable_relocated": "CallableRelocated",
                 "data": "Data"}.get(r["status"], "CommentOnly"),
                r["reason"].replace('"', "'"), r["note"].replace('"', "'"), r["rva"], r["sha256"]))
c.append("};")
c.append("const std::size_t kBlockCount = sizeof(kBlocks) / sizeof(kBlocks[0]);")
c.append("")
c.append("}  // namespace embedded")
c.append("}  // namespace lcns")
io.open(OUT_CPP, "w", encoding="utf-8", newline="\n").write("\n".join(c) + "\n")

# ------------------------------------------------------------ gen_table.cpp
# The pointer table lives in its own translation unit because it is the only thing that references the assembly
# symbols: if a toolchain cannot assemble gen_orig.S, the build drops just this file and everything else still links.
t = []
t.append("// generated by re/g_embed.py -- do not edit by hand.")
t.append("//")
t.append("// Addresses of the executable copies in gen_orig.S, in the registry's callable order. Only this translation")
t.append("// unit references the assembly symbols, so a toolchain without ASM support can drop it and still link.")
t.append('#include "lcns/embedded.hpp"')
t.append("")
t.append("// Each symbol is declared as a C function with no parameters: that is what gives &symbol the type RawFn.")
t.append("extern \"C\" {")
for r in callable_rows:
    t.append("void %s();" % r["symbol"])
t.append("}")
t.append("")
t.append("namespace lcns {")
t.append("namespace embedded {")
t.append("")
t.append("#if defined(LCNS_HAS_EMBEDDED_ASM)")
t.append("const RawFn kOrigTable[] = {")
for r in callable_rows:
    t.append("    &%s,  // 0x%x  %s" % (r["symbol"], r["rva"], r["note"]))
t.append("};")
t.append("const std::size_t kOrigTableCount = sizeof(kOrigTable) / sizeof(kOrigTable[0]);")
t.append("#else")
t.append("// No assembler: the bytes are still embedded as data, but nothing can be executed from them.")
t.append("const RawFn kOrigTable[] = {nullptr};")
t.append("const std::size_t kOrigTableCount = 0;")
t.append("#endif")
t.append("")
t.append("}  // namespace embedded")
t.append("}  // namespace lcns")
io.open(os.path.join(LC, r"src\embedded\gen_table.cpp"), "w", encoding="utf-8", newline="\n").write(
    "\n".join(t) + "\n")

# ------------------------------------------------------------ registry json
io.open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(json.dumps(
    [{"rva": r["rva"], "size": r["size"], "symbol": r["symbol"], "status": r["status"],
      "reason": r["reason"], "note": r["note"], "relocations": r.get("relocations", []),
      "callers": r["callers"], "sha256": r["sha256"]} for r in rows],
    indent=2, ensure_ascii=False) + "\n")

# ---------------------------------------------------------------- EMBEDDED.md
m = []
m.append("# Embedded original code")
m.append("")
m.append("Generated by `re/g_embed.py` from `libcns_dump_64.dll`. Every block below is domain code this work read but has")
m.append("**not** reimplemented in C++; its original bytes now live in the project, and `re/check_embeddings.py` re-reads")
m.append("the DLL and fails if any byte or hash drifts.")
m.append("")
m.append("A block is **callable** when it has no RIP-relative memory operand, no call or jump leaving it and no absolute")
m.append("image address: then it is position-independent and the test can call it, which is what makes a differential test")
m.append("against a C++ reimplementation possible. Otherwise it is **comment_only**, with the reason recorded.")
m.append("")
m.append("| rva | bytes | status | callers | note |")
m.append("|---|---:|---|---:|---|")
for r in rows:
    m.append("| `0x%x` | %d | %s | %d | %s |" % (r["rva"], r["size"], r["status"], r["callers"], r["note"]))
m.append("")
m.append("%d blocks, %d callable, %d comment-only, %d bytes of original code embedded."
         % (len(rows), len(callable_rows), len(rows) - len(callable_rows), sum(r["size"] for r in rows)))
m.append("")
for r in rows:
    m.append("## `0x%x` -- %s" % (r["rva"], r["note"]))
    m.append("")
    m.append("- size %d bytes, %d callers, status **%s**" % (r["size"], r["callers"], r["status"]))
    if r["reason"]:
        m.append("- not callable because: %s" % r["reason"])
    m.append("- sha256 `%s`" % r["sha256"])
    m.append("")
    if r["listing"]:
        m.append("```asm")
        m.extend(r["listing"] if r["size"] <= 4096 else r["listing"][:4096] + ["... listing truncated ..."])
        m.append("```")
    else:
        m.append("```")
        m.append("; data block, %d bytes; first bytes as hex: %s"
                 % (r["size"], " ".join("%02x" % x for x in r["bytes"][:16])))
        m.append("```")
    m.append("")
io.open(OUT_MD, "w", encoding="utf-8", newline="\n").write("\n".join(m) + "\n")

data_rows = [r for r in rows if r["status"] == "data"]
print("blocks: %d (%d callable, %d comment_only, %d data), %d bytes"
      % (len(rows), len(callable_rows),
         len(rows) - len(callable_rows) - len(data_rows), len(data_rows),
         sum(r["size"] for r in rows)))
print("")
print("%-10s %6s %-13s %7s  %s" % ("rva", "bytes", "status", "callers", "note"))
for r in rows:
    print("0x%-8x %6d %-13s %7d  %s" % (r["rva"], r["size"], r["status"], r["callers"], r["note"][:52]))
print("")
for r in rows:
    if r["covered"] < r["rva"] + r["size"]:
        print("WARNING 0x%x: disassembly covers only up to 0x%x of 0x%x"
              % (r["rva"], r["covered"], r["rva"] + r["size"]))
