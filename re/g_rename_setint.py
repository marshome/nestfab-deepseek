# -*- coding: utf-8 -*-
"""Rename `setInt_1FC` to `setLocalMaximumIterations`: the export's own name is the oracle and the offset-derived name is the shape this objective removes.

**WHAT THE TREE HAS**: `void setInt_1FC(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field1FC = ...; }` with the comment `// RE 0x0D400 -> +0x1FC`,
and `kForwarding` names it at ordinal 84.

**AND `0x0D400` IS `SetLocalMaximumIterations`** -- the module's own export name, and the same function writes `Order`'s `maxIterations` at the same offset. **So
`setInt_1FC` is a name built from a position and `setLocalMaximumIterations` is the name the module gives it**, which is the difference between a placeholder and
an oracle.

**AND THE TWO BODIES ARE THE SAME STORE**, so this is a rename rather than a second implementation: `IntFieldCarrier::field1FC` and `LocalEngineCarrier::maxIterations`
are both `+0x1FC`, and keeping both would be exactly the "second description of one thing" the objective forbids. **One function, one name, and the name is the
module's.**
"""
import io
import sys

IMPL = r"D:\Nesting\nestfab\lcns\src\exports_impl.cpp"
HEADER = r"D:\Nesting\nestfab\lcns\include\lcns\exports_impl.hpp"
FWD = r"D:\Nesting\nestfab\lcns\include\lcns\detail\exports_forwarding.inc"


def patch(path, pairs, label):
    text = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    changed = 0
    for old, new in pairs:
        if new in text and old not in text:
            continue
        if old not in text:
            print("   %-18s anchor not found: %s" % (label, old.strip().split("\n")[0][:60]))
            continue
        text = text.replace(old, new, 1)
        changed += 1
    if changed:
        io.open(path, "w", encoding="utf-8", newline="\n").write(text)
    print("   %-18s %d replacement(s)" % (label, changed))


def main():
    patch(HEADER, [
        ("void setInt_1FC(void* order, int value);           // RE 0x0D400 -> +0x1FC\n", ""),
    ], "exports_impl.hpp")

    patch(IMPL, [
        ("void setInt_1FC(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field1FC = value; }",
         ""),
    ], "exports_impl.cpp")

    patch(FWD, [
        ("&lcns::dll::exports::impl::setInt_1FC", "&lcns::dll::exports::impl::setLocalMaximumIterations"),
    ], "exports_forwarding.inc")
    return 0


if __name__ == "__main__":
    sys.exit(main())
