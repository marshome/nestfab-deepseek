# -*- coding: utf-8 -*-
"""For each setter, the RE addresses its body cites, the store, and `Order`'s name at that offset.

**THE BODY CARRIES THE ADDRESSES INLINE** -- `// RE 0xF225: mov byte [rsi + 0x98], 1` -- **so the comment is both the index and the evidence**, and no comment block
above the function is needed. The two earlier versions looked above the function and found nothing.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
sys.path.insert(0, os.path.join(ROOT, "re"))

from lib import disasm, load_prof  # noqa: E402

STORE = re.compile(r"^(byte|word|dword|qword|xmmword) ptr \[(\w+)(?: \+ (0x[0-9a-f]+))?\],")
WIDTH = {"byte": 1, "word": 2, "dword": 4, "qword": 8, "xmmword": 16}


def order_fields():
    text = io.open(os.path.join(ROOT, "lcns", "include", "lcns", "model.hpp"), encoding="utf-8", errors="replace").read()
    body = re.search(r"struct Order\s*\{(.*?)\n\};", text, re.S).group(1)
    out = {}
    for line in body.split("\n"):
        found = re.search(r"\+0x([0-9A-Fa-f]+)", line)
        field = re.match(r"\s*([\w:<>,\s\*&]+?)\s+(\w+)\s*(?:\[[^\]]*\])?\s*[;=]", line)
        if found and field:
            out[int(found.group(1), 16)] = (field.group(2), field.group(1).strip())
    return out


def main():
    names = order_fields()
    impl = io.open(os.path.join(ROOT, "lcns", "src", "exports_impl.cpp"), encoding="utf-8", errors="replace").read()
    profile = load_prof()

    print("%-40s %-20s %-26s %s" % ("implementation", "stores", "at", "Order's field there"))
    for match in re.finditer(r"^(?:void|std::[\w:]+|const char\*|unsigned\w*)\s+(\w+)\s*\(([^)]*)\)\s*\{", impl, re.M):
        function = match.group(1)
        end = impl.find("\n}", match.end())
        body = impl[match.end():end if end > 0 else len(impl)]
        found_store = None
        for line in body.split("\n"):
            offset = re.search(r"\[r\w+ \+ (0x[0-9a-f]+)\]", line)
            kind = re.search(r"\b(byte|word|dword|qword) ptr \[", line)
            if offset and kind:
                found_store = (int(offset.group(1), 16), kind.group(1))
                break
        if not found_store:
            continue
        offset, kind = found_store
        field, type_name = names.get(offset, ("** Order has no name here **", "?"))
        print("%-40s %-20s %-26s %s"
              % (function[:40], kind, "+0x%X = %d byte" % (offset, WIDTH[kind]), "%s  %s" % (field, type_name)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
