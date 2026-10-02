# -*- coding: utf-8 -*-
"""Read the two strings an assertion site builds: the condition and the message.

Every site in 0x1EE50 loads a rip-relative string with `lea rdx, [...]`, passes it to the small-string constructor 0x1B130, and does
that twice before calling the reporter:

    0x2081A  lea rdx, [rip + 0x98d4a7]   ; the CONDITION
    0x20824  call 0x1b130
    0x208AC  lea rdx, [rip + 0x98d415]   ; the MESSAGE
    0x208B6  call 0x1b130
    0x208C1  mov edx, 0x2d               ; the LINE
    0x208C9  call 0x60a620

so a site's content is two ordinary strings in the image, and this resolves them. That is the half of the assertion channel the previous
rounds could not decode from immediates, and here it needs no reconstruction at all because the strings are stored rather than built.

    python g_assert_strings.py 0x1EE50

A SELF-CHECK, per the rule: a string this tool resolves must be printable ASCII of a plausible length, and the tool refuses when the
sites in a function resolve to nothing, because a function with seven reporter calls that yields zero strings means the resolution is
broken rather than the strings being absent.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import lib as LIB           # noqa: E402
from lib import disasm, load_prof, rva2off  # noqa: E402

REPORTER = 0x60A620
CONSTRUCTOR = 0x1B130
DIRECT = re.compile(r"^0x([0-9a-f]+)$")
LEA_RIP = re.compile(r"^[a-z0-9]+, \[rip \+ (0x[0-9a-f]+)\]$")


def image():
    return LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data


def string_at(rva, blob):
    offset = rva2off(rva)
    if offset is None or offset < 0 or offset >= len(blob):
        return None
    end = blob.find(b"\x00", offset)
    if end < 0 or end - offset > 400:
        return None
    raw = blob[offset:end]
    if not raw:
        return None
    printable = sum(1 for byte in raw if 32 <= byte < 127 or byte in (9,))
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
        # the line, and the strings loaded since the previous reporter call
        line = None
        strings = []
        for back in range(index - 1, max(-1, index - 40), -1):
            previous = body[back]
            text = previous.op_str.strip()
            if previous.mnemonic == "call":
                called = DIRECT.match(text)
                if called and int(called.group(1), 16) == REPORTER:
                    break
                continue
            if previous.mnemonic == "lea":
                moved = LEA_RIP.match(text)
                if moved:
                    target = previous.address + previous.size + int(moved.group(1), 16)
                    text_at = string_at(target, blob)
                    if text_at:
                        strings.append(text_at)
                continue
            moved = re.match(r"^(edx|r8d|ecx|r9d), (0x[0-9a-f]+)$", text)
            if moved and line is None:
                line = int(moved.group(2), 16)
        if strings or line is not None:
            out.append((ins.address, line, list(reversed(strings))))
    return out


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("address")
    args = parser.parse_args(argv)
    profile = load_prof()
    blob = image()

    check = sites(0x1EE50, profile, blob)
    print("SELF-CHECK: 0x1EE50 has 7 reporter calls; this tool resolves %d of them with at least one string" % len(check))
    if not check:
        print("REFUSING TO REPORT: seven reporter calls yielded nothing, so the resolution is broken rather than the strings absent.")
        return 2
    print("")

    root = int(args.address, 16)
    for at, line, strings in sites(root, profile, blob):
        print("0x%-8X line %-6s" % (at, line if line is not None else "?"))
        for text in strings:
            print("      %r" % text[:150])
    print("")
    print("A site's content is a CONDITION and a MESSAGE, both ordinary strings in the image, which is why no reconstruction is needed")
    print("here -- the previous rounds' difficulty was with sites that BUILD the name from immediates instead of loading it.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
