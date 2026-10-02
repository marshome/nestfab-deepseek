# -*- coding: utf-8 -*-
"""Decode the FILE NAME at every assertion site: by rip-relative lea, or by immediate stores.

Two forms occur, and the previous round established both:

  * 0x1EE50 calls 0x1B130 with a `lea rdx, [rip + disp]` pointing at the name, so the name is an ordinary string in the image;
  * 0x526160 assembles the name with `movabs` and small stores into a std::string's inline storage, so the name exists only as
    immediates.

This resolves the first form by computing the target of the lea and reading a NUL-terminated string, and the second by collecting the
immediate stores in program order as before. It then groups every assertion site by file, which is the view that makes the map useful:
"which functions assert in part.cpp" is a question about a translation unit.

Usage: python g_assert_files.py [--top 20]
Output: re/assert_files.json

A SELF-CHECK against a name already on record: 0x526160's site must decode to a name ending in "stat.cpp" with line 154, because an
earlier round read exactly that by hand.
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
STORE_MEM = re.compile(r"^(byte|word|dword|qword) ptr \[[^\]]+\], (0x[0-9a-f]+)$")
MOVE_IMM = re.compile(r"^([a-z0-9]+), (0x[0-9a-f]+)$")
LINE_REGS = ("edx", "r8d", "ecx", "r9d", "esi", "edi")
PRINTABLE = re.compile(rb"[\x20-\x7e]{4,}")

# A 16 or 32 bit register is the same register as its 64 bit form, and `word ptr [rax+0x14], dx` carries two bytes of a name held in
# rdx. The first version tested exact names, so that store was skipped and the name lost its tail.
ALIAS = {}
for _full, _names in {"rax": ("eax", "ax", "al"), "rbx": ("ebx", "bx", "bl"), "rcx": ("ecx", "cx", "cl"),
                      "rdx": ("edx", "dx", "dl"), "rsi": ("esi", "si", "sil"), "rdi": ("edi", "di", "dil"),
                      "rbp": ("ebp", "bp", "bpl"), "rsp": ("esp", "sp", "spl")}.items():
    ALIAS[_full] = _full
    for _name in _names:
        ALIAS[_name] = _full
for _r in range(8, 16):
    for _suffix in ("", "d", "w", "b"):
        ALIAS["r%d%s" % (_r, _suffix)] = "r%d" % _r


def canonical(register):
    return ALIAS.get(register, register)


def image():
    return LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data


def string_at(rva, blob):
    offset = rva2off(rva)
    if offset is None or offset < 0 or offset >= len(blob):
        return None
    end = blob.find(b"\x00", offset)
    if end < 0:
        return None
    raw = blob[offset:end]
    if not raw or len(raw) > 200 or not PRINTABLE.match(raw):
        return None
    return raw.decode("ascii", "replace")


def line_at(body, index):
    for back in range(index - 1, max(-1, index - 60), -1):
        previous = body[back]
        if previous.mnemonic not in ("mov", "movabs"):
            continue
        moved = MOVE_IMM.match(previous.op_str.strip())
        if not moved:
            continue
        register, value = moved.group(1), int(moved.group(2), 16)
        if register in LINE_REGS and value < 100000:
            return value
    return None


def file_at(body, index, blob):
    """The file name a site names, by either form. Returns None when neither is found.

    THE BYTES ARE COLLECTED ONE INSTRUCTION AT A TIME, and the width comes from the instruction rather than from the VALUE. A first
    version guessed the width from how large the immediate was, which decoded `0x7070` as four bytes instead of two and produced a
    one-character name. The store's own size is the fact: `movabs` writes eight, `mov qword ptr` eight, `mov dword ptr` four, `mov word
    ptr` two, `mov byte ptr` one.
    """
    pieces = []          # (program order index, byte offset within the buffer or None, the bytes)
    pending = {}         # canonical register -> (program order index, bytes) from the nearest preceding move
    # THE RUN STOPS AT THE FIRST INSTRUCTION THAT IS NOT PART OF THE NAME. A first version collected everything in a sixty instruction
    # window, which swept in an earlier string ("unbound nesting") and stack temporaries holding lengths, and the reconstruction began
    # with 0x1B -- a byte count, not a byte of the name. What makes an instruction part of the name is that it is a store into memory or
    # a move of an immediate into a register; anything else ends the run.
    for back in range(index - 1, max(-1, index - 60), -1):
        previous = body[back]
        text = previous.op_str.strip()
        if previous.mnemonic == "lea":
            moved = LEA_RIP.match(text)
            if moved:
                target = previous.address + previous.size + int(moved.group(1), 16)
                name = string_at(target, blob)
                if name and ("." in name or "/" in name or "\\" in name):
                    return name
            break
        if previous.mnemonic not in ("mov", "movabs"):
            break
        # a move into a register: remember it as a possible source for a later store. NO VALUE FILTER -- an earlier version kept only
        # immediates above 0x100 and the two-byte "pp" fell out of the name.
        moved = MOVE_IMM.match(text)
        if moved:
            register = canonical(moved.group(1))
            if register in pending and register not in LINE_REGS:
                # a register that already holds a piece of the name is being RE-loaded with the next piece, which is how the two
                # movabs instructions work: rdx carries "../struc" and then "ture\sta". So this is a store as well as a move.
                _at, chunk = pending[register]
                pieces.append((back, None, chunk))
                width = 8 if previous.mnemonic == "movabs" else (4 if int(moved.group(2), 16) > 0xFFFF else 2)
                pending[register] = (back, int(moved.group(2), 16).to_bytes(width, "little"))
            elif register not in LINE_REGS:
                value = int(moved.group(2), 16)
                width = 8 if previous.mnemonic == "movabs" else (4 if value > 0xFFFF else (2 if value > 0xFF else 1))
                pending[register] = (back, value.to_bytes(width, "little"))
            continue
        stored = STORE_MEM.match(text)
        if not stored:
            break
        width = {"qword": 8, "dword": 4, "word": 2, "byte": 1}[stored.group(1)]
        source = re.search(r",\s*([a-z0-9]+)$", text)
        destination = re.search(r"\[[a-z0-9]+(?:\s*\+\s*(0x[0-9a-f]+))?\]", text)
        offset = int(destination.group(1), 16) if destination and destination.group(1) else None
        # The chunk is the pending value of the SOURCE REGISTER when that register was just loaded with a piece of the name, and
        # otherwise the immediate the store carries. A register that was restored from the stack is neither, and taking it would
        # splice unrelated bytes into the name -- which is how the first version produced a one-character result.
        chunk = None
        source = re.search(r",\s*([a-z0-9]+)$", text)
        if source and canonical(source.group(1)) in pending:
            _at, chunk = pending[canonical(source.group(1))]
            chunk = chunk[:width]
        if chunk is None:
            chunk = int(stored.group(2), 16).to_bytes(width, "little")
        pieces.append((back, offset, chunk))
    if not pieces:
        return None
    # THE PIECES ARE IN REVERSE PROGRAM ORDER because the walk goes backwards, and the buffer is rebuilt in program order by
    # reversing. Each piece carries the DESTINATION offset when the store named one -- `mov [rax+8], rdx` puts its bytes at 8 -- and
    # appends otherwise, which is what the two movabs stores and the final two-byte store between them produce.
    raw = bytearray()
    for _back, offset, chunk in pieces:
        if offset is None or offset >= len(raw):
            raw.extend(chunk)
        else:
            raw[offset:offset + len(chunk)] = chunk
    name = bytes(raw).split(b"\x00")[0]
    text = "".join(chr(b) if 32 <= b < 127 else "." for b in name)
    return text if ("." in text or "/" in text or "\\" in text) else None


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args(argv)
    profile = load_prof()
    blob = image()

    callers = sorted(set((profile.get(REPORTER) or {}).get("callers") or []))

    def sites_in(address):
        size = (profile.get(address) or {}).get("size") or 0
        body = [i for i in disasm(address) if i.address < address + size]
        out = []
        for index, ins in enumerate(body):
            if ins.mnemonic != "call":
                continue
            match = DIRECT.match(ins.op_str.strip())
            if match and int(match.group(1), 16) == REPORTER:
                out.append((ins.address, line_at(body, index), file_at(body, index, blob)))
        return out

    # ---- the self-check against a name read by hand ----------------------------------------------------------------------
    check = [entry for entry in sites_in(0x526160) if entry[1] == 154]
    print("SELF-CHECK: 0x526160's line-154 site names %r (an earlier round read a name ending in stat.cpp)"
          % (check[0][2] if check else None))
    if not check or not check[0][2] or not check[0][2].endswith("stat.cpp"):
        print("REFUSING TO REPORT: the name for the one site read by hand is not reproduced, so the map would be worthless.")
        return 2
    print("")

    by_file = collections.Counter()
    by_function = collections.Counter()
    named = 0
    total = 0
    payload = {}
    for address in callers:
        sites = sites_in(address)
        if not sites:
            continue
        entries = []
        for at, line, name in sites:
            total += 1
            if name:
                named += 1
                by_file[name] += 1
                by_function[(name, address)] += 1
            entries.append({"site": "0x%X" % at, "line": line, "file": name})
        payload["0x%X" % address] = entries

    with io.open(os.path.join(HERE, "assert_files.json"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"sites": payload}, indent=1, sort_keys=True))

    print("assertion sites: %d, of which %d name a file" % (total, named))
    print("")
    print("the files, by how many assertions name them:")
    for name, count in by_file.most_common(args.top):
        functions = sum(1 for (n, _a) in by_function if n == name)
        print("   %-44s %4d sites in %3d functions" % (name[:44], count, functions))
    print("")
    print("wrote re/assert_files.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
