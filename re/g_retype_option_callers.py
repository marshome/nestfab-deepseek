# -*- coding: utf-8 -*-
"""Point the eight wrappers at the typed implementations, converting the ABI handle at the boundary.

**THE HANDLE IS `lcns::dll::Order_t*` AND THE CLASS IS `lcns::Order`**, so the conversion has to be a `reinterpret_cast` and it has to be AT THE BOUNDARY -- once per
call, in the wrapper -- rather than the implementation taking `void*` and casting inside. **That is what makes the implementation's signature say what it writes.**
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API = r"D:\Nesting\nestfab\lcns\src\api_exports.cpp"

FUNCTIONS = ["setFillLastNestingStrategy", "setFloatingMode", "setOriginPackingMode",
             "setEvaluateIntermediateNestingsAsLast", "setReorganizeBiggestPartNearOrigin",
             "setReorganizeLongestPartNearOrigin", "setPartialShearMode", "setPartCommonCutMode"]


def main(apply):
    text = io.open(API, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    done = 0
    for name in FUNCTIONS:
        pattern = re.compile(r"impl::%s\(static_cast<void\*>\((\w+)\), (\w+)\)" % re.escape(name))
        text, count = pattern.subn(r"impl::%s(reinterpret_cast<lcns::Order*>(\1), \2)" % name, text)
        print("   %-42s %d caller(s)" % (name, count))
        done += count
    if apply and done:
        io.open(API, "w", encoding="utf-8", newline="\n").write(text)
        print("%d call(s) written" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
