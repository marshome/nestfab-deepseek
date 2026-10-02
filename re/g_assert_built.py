# -*- coding: utf-8 -*-
"""The BUILT form of an assertion string: the name assembled from immediates, decoded by register tracking.

0x526160 builds "../structure\\stat.cpp" from three stores into an object's inline storage, and an earlier round decoded it by hand:

    0x52637C  movabs rdx, 0x63757274735c2e2e    ; "../struc"  -> [rax]
    0x526389  movabs rdx, 0x6174735c65727574    ; "ture\\sta"  -> [rax+8]
    0x526397  mov    edx, 0x7070                ; "pp" - AND THE LINE REGISTER IS REUSED FOR IT
    0x52639C  mov    word [rax + 0x14], dx
    0x5263A5  mov    dword [rax + 0x10], 0x632e7374  ; "ts.c"
    0x5263BA  mov    edx, 0x9a                  ; and only NOW the line number

The previous attempt at this failed six times because it walked backwards and STOPPED at the first assignment to a line register, which
that `mov edx, 0x7070` is. The fix is to walk FORWARD from the point where the message buffer is established, which is why this tool
looks for the ALLOCATION of the buffer rather than for the reporter call.

A SELF-CHECK, per the rule, against the one site read by hand: 0x526160's message must come out as a name ending in stat.cpp.
"""
import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

REPORTER = 0x60A620
ALLOCATOR = 0x910BA0
DIRECT = re.compile(r"^0x([0-9a-f]+)$")
STORE = re.compile(r"^(byte|word|dword|qword) ptr \[([a-z0-9]+)(?:\s*\+\s*(0x[0-9a-f]+))?\], (.+)$")
MOVE_IMM = re.compile(r"^([a-z0-9]+), (0x[0-9a-f]+)$")
LINE_REGS = ("edx", "r8d", "ecx", "r9d", "esi", "edi")


def canonical(register):
    table = {"eax": "rax", "ax": "rax", "al": "rax", "ebx": "rbx", "bx": "rbx", "bl": "rbx",
             "ecx": "rcx", "cx": "rcx", "cl": "rcx", "edx": "rdx", "dx": "rdx", "dl": "rdx",
             "esi": "rsi", "si": "rsi", "edi": "rdi", "di": "rdi"}
    return table.get(register, register)


def built_string(body, call_index):
    """Walk FORWARD from the allocation of the message buffer to the reporter call."""
    start = None
    for back in range(call_index - 1, max(-1, call_index - 30), -1):
        previous = body[back]
        if previous.mnemonic == "call":
            match = DIRECT.match(previous.op_str.strip())
            if match and int(match.group(1), 16) == ALLOCATOR:
                start = back
                break
    if start is None:
        return None, None
    # the buffer's register: the destination of a `mov reg, rax` right after the allocation, OR rax itself when the code uses it in
    # place. At 0x526160 the sequence is `call 0x910BA0` then `mov rdx, [rsp+0x28]`, so the buffer STAYS in rax and the first version,
    # which required a `mov reg, rax`, found no buffer register and returned nothing.
    buffer_reg = None
    for forward in range(start + 1, min(start + 4, len(body))):
        moved = re.match(r"^([a-z0-9]+), rax$", body[forward].op_str.strip())
        if moved:
            buffer_reg = canonical(moved.group(1))
            break
    if buffer_reg is None:
        buffer_reg = "rax"

    cells = {}
    immediates = {}
    line = None
    for index in range(start + 1, call_index):
        ins = body[index]
        text = ins.op_str.strip()
        if ins.mnemonic in ("mov", "movabs"):
            moved = MOVE_IMM.match(text)
            if moved:
                register = canonical(moved.group(1))
                value = int(moved.group(2), 16)
                immediates[register] = value
                if moved.group(1) in LINE_REGS:
                    line = value
                continue
            stored = STORE.match(text)
            if stored:
                width = {"byte": 1, "word": 2, "dword": 4, "qword": 8}[stored.group(1)]
                base = canonical(stored.group(2))
                if base != buffer_reg:
                    continue
                offset = int(stored.group(3), 16) if stored.group(3) else 0
                source = stored.group(4).strip()
                value = None
                if source in ("rax", "rdx", "rcx", "rbx", "rsi", "rdi", "r8", "r9", "r10", "r11",
                              "eax", "edx", "ecx", "ebx", "esi", "edi", "ax", "dx", "cx", "bx", "si", "di",
                              "al", "dl", "cl", "bl"):
                    value = immediates.get(canonical(source))
                else:
                    immediate = re.match(r"^(0x[0-9a-f]+)$", source)
                    if immediate:
                        value = int(immediate.group(1), 16)
                if value is None:
                    continue
                cells[offset] = value.to_bytes(width, "little")
                continue
        if ins.mnemonic == "call":
            match = DIRECT.match(text)
            if match and int(match.group(1), 16) == REPORTER:
                break
    if not cells:
        return None, line
    highest = max(cells)
    raw = bytearray(highest + len(cells[highest]))
    for offset, chunk in cells.items():
        raw[offset:offset + len(chunk)] = chunk
    name = bytes(raw).split(b"\x00")[0]
    text = "".join(chr(byte) if 32 <= byte < 127 else "." for byte in name)
    return (text or None), line


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("address", nargs="?", default="0x526160")
    args = parser.parse_args(argv)
    profile = load_prof()
    root = int(args.address, 16)
    size = (profile.get(root) or {}).get("size") or 0
    body = [i for i in disasm(root) if i.address < root + size]

    results = []
    for index, ins in enumerate(body):
        if ins.mnemonic != "call":
            continue
        match = DIRECT.match(ins.op_str.strip())
        if match and int(match.group(1), 16) == REPORTER:
            results.append((ins.address,) + built_string(body, index))

    print("0x%X: %d reporter call(s)" % (root, len(results)))
    for at, text, line in results:
        print("   0x%-8X line %-6s %r" % (at, line if line is not None else "?", text))
    print("")

    if root == 0x526160:
        ok = results and results[0][1] and results[0][1].endswith("stat.cpp")
        print("SELF-CHECK: 0x526160's built message ends in stat.cpp?  %s" % bool(ok))
        if not ok:
            print("REFUSING: the one built string read by hand is not reproduced.")
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
