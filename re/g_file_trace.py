# -*- coding: utf-8 -*-
"""Trace the file-name decoder on the one site whose answer is known."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.dirname(HERE))

import g_assert_files as G          # noqa: E402
from lib import disasm, load_prof   # noqa: E402


def main():
    profile = load_prof()
    blob = G.image()
    size = (profile.get(0x526160) or {}).get("size") or 0
    body = [i for i in disasm(0x526160) if i.address < 0x526160 + size]
    index = [k for k, i in enumerate(body) if i.mnemonic == "call" and i.op_str.strip() == "0x60a620"][0]
    print("call index %d" % index)
    pieces = []
    pending = {}
    for back in range(index - 1, max(-1, index - 60), -1):
        previous = body[back]
        text = previous.op_str.strip()
        if previous.mnemonic == "lea":
            moved = G.LEA_RIP.match(text)
            if moved:
                target = previous.address + previous.size + int(moved.group(1), 16)
                print("[%d] LEA -> rva 0x%X  str=%r" % (back, target, G.string_at(target, blob)))
            continue
        if previous.mnemonic not in ("mov", "movabs"):
            continue
        moved = G.MOVE_IMM.match(text)
        if moved:
            register = moved.group(1)
            if register not in G.LINE_REGS:
                value = int(moved.group(2), 16)
                width = 8 if previous.mnemonic == "movabs" else (4 if value > 0xFFFF else (2 if value > 0xFF else 1))
                chunk = value.to_bytes(width, "little")
                pending[register] = (back, chunk)
                print("[%d] MOVE %s <- 0x%X width=%d -> %r" % (back, register, value, width, chunk))
            continue
        stored = G.STORE_MEM.match(text)
        if not stored:
            continue
        width = {"qword": 8, "dword": 4, "word": 2, "byte": 1}[stored.group(1)]
        source = re.search(r",\s*([a-z0-9]+)$", text)
        destination = re.search(r"\[[a-z0-9]+(?:\s*\+\s*(0x[0-9a-f]+))?\]", text)
        offset = int(destination.group(1), 16) if destination and destination.group(1) else None
        chunk = None
        if source and source.group(1) in pending:
            _at, chunk = pending[source.group(1)]
            chunk = chunk[:width]
            print("[%d] STORE %s <- reg %s off=%s chunk=%r" % (back, stored.group(1), source.group(1), offset, chunk))
        if chunk is None:
            chunk = int(stored.group(2), 16).to_bytes(width, "little")
            print("[%d] STORE %s <- IMM 0x%s off=%s chunk=%r" % (back, stored.group(1), stored.group(2), offset, chunk))
        pieces.append((back, offset, chunk))
    pieces.sort()
    raw = bytearray()
    for _back, offset, chunk in pieces:
        if offset is None or offset >= len(raw):
            raw.extend(chunk)
        else:
            raw[offset:offset + len(chunk)] = chunk
    print("RAW: %r" % bytes(raw))
    return 0


if __name__ == "__main__":
    sys.exit(main())
