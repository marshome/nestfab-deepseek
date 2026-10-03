# -*- coding: utf-8 -*-
"""Report the REAL forwarding state, and correct the count this project has been quoting.

**`re/g_export_status.py` COUNTED THE WRONG CALL.** It looked for `exports_impl::` and found zero, which is true and misleading: **the wrappers that forward call
`impl::`**, in the namespace `lcns::dll::exports::impl`, and `kForwarding` in `lcns/include/lcns/detail/exports_forwarding.inc` holds 47 entries keyed by ordinal.
`Status` is not a literal in the table at all -- `exports.cpp`'s `statusOf` derives it from `forwards(index)`. **So "zero dispatching wrappers" was a wrong claim
made by a grep, and it was reported to the human twice.**
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
FWD = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")


def main():
    api = io.open(API, encoding="utf-8", errors="replace").read()
    forwarding = io.open(FWD, encoding="utf-8", errors="replace").read()

    rows = re.findall(r'\{"([^"]+)",\s*(\d+),\s*(\d+),\s*0x([0-9A-Fa-f]+)u,\s*(\d+)u,\s*Status::(\w+)', api)
    entries = re.findall(r"^\s*\{(\d+),\s*reinterpret_cast<void\*>\(&([\w:]+)\)\}", forwarding, re.M)
    impl_calls = len(re.findall(r"impl::", api))
    exports_impl_calls = len(re.findall(r"exports_impl::", api))
    stubs = len(re.findall(r"notReversed\(", api))

    print("exports in the table:                          %d" % len(rows))
    print("kForwarding entries (KEYED BY ORDINAL):        %d" % len(entries))
    print("")
    print("wrappers that call `impl::` (the forwarders):  %d" % impl_calls)
    print("wrappers that call `exports_impl::`:           %d      <- the count that was quoted and is the WRONG NAME" % exports_impl_calls)
    print("wrappers that only call notReversed():         %d" % stubs)
    print("")
    print("**AND `Status` IS DERIVED AND NOT A LITERAL.** `lcns/src/exports.cpp`'s `statusOf(index)` returns `forwards(index) ? Status::Forwarded :")
    print("Status::NotReversed`, and `forwards` searches `kForwarding` by ordinal. **So the status column in the table is documentation and the mechanism is the")
    print("forwarding list** -- which means the question to ask is how many IMPORTANT exports are missing from that list, not how many string literals say NotReversed.")
    print("")
    print("the four ordinals I touched this round and whether the list has them:")
    for ordinal in (84, 82, 73, 268):
        present = any(int(entry[0]) == ordinal for entry in entries)
        print("   ordinal %-4d %s" % (ordinal, "in kForwarding" if present else "**NOT in kForwarding**"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
