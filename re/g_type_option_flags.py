# -*- coding: utf-8 -*-
"""Replace the eight `OptionFlagCarrier` implementations with the real `Order*`.

**THE CARRIER IS NOW A SECOND DESCRIPTION OF FIELDS `Order` HAS.** Seven of its flags are named in `Order` -- from the exports that write them -- and `+0x44` and
`+0x48` have had their width measured as thirty-two bits. So every one of these eight functions can name the real field, and the carrier keeps nothing that `Order`
does not already say.

**AND ONE OF THEM IS A REAL BUG FIX, NOT A RENAME.** `setPartialShearMode` writes `field48` and `field44` as `std::uint32_t` into a carrier; `Order`'s `shear` and
`shearCorner` are `std::uint32_t` now, so the assignment type-checks **and the byte-level field it used to sit beside is gone**.

**AND `setPartCommonCutMode` WRITES THE LOW BYTE OF `field1C`.** RE 0xDE69 is `setne byte [rsi + 0x1c]` and RE 0xD357 is `mov dword [rsi + 0x1c], ebx` -- two views of
one address. **A byte member there would alias the dword**, so the write is expressed through the dword's low byte with `& 0xFF` and the reason is on the line.
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
IMPL = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")

BODIES = {
    "setFillLastNestingStrategy": ("Order* order, int value",
        "order->fillLastNestingStrategy = (value != 0);   // RE 0xDDA9: setne byte [rsi + 0x40]"),
    "setFloatingMode": ("Order* order, int value",
        "order->floatingMode = (value != 0);   // RE 0xDD49: setne byte [rsi + 0x20]"),
    "setOriginPackingMode": ("Order* order, int value",
        "order->originPackingMode = (value != 0);   // RE 0xDD79: setne byte [rsi + 0x21]"),
    "setEvaluateIntermediateNestingsAsLast": ("Order* order, int value",
        "order->evaluateIntermediateNestingsAsLast = (value != 0);   // RE 0x1045F: setne byte [rbx + 0x41]"),
    "setReorganizeBiggestPartNearOrigin": ("Order* order, int value",
        "order->reorganizeBiggestPartNearOrigin = (value != 0);   // RE 0x1048F: setne byte [rbx + 0x22]"),
    "setReorganizeLongestPartNearOrigin": ("Order* order, int value",
        "order->reorganizeLongestPartNearOrigin = (value != 0);   // RE 0x104BF: setne byte [rbx + 0x23]"),
    "setPartialShearMode": ("Order* order, int value",
        "order->shearCorner = static_cast<std::uint32_t>(value);   // RE 0xDE07: mov dword [rsi + 0x48], ebx\n"
        "    order->shear = static_cast<std::uint32_t>(value);         // RE 0xDE0A: mov dword [rsi + 0x44], ebx, the same field setShearMode writes"),
    "setPartCommonCutMode": ("Order* order, int value",
        "// **THE LOW BYTE OF `field1C` AND NOT A FIELD OF ITS OWN.** RE 0xDE69 is `setne byte [rsi + 0x1c]` while RE 0xD357 is `mov dword [rsi + 0x1c], ebx` -- two\n"
        "    // views of one address, so a byte member here would alias the dword and the compiler would not say so.\n"
        "    order->field1C = (order->field1C & 0xFFFFFF00u) | static_cast<std::uint32_t>(value != 0);   // RE 0xDE69"),
}


def main(apply):
    impl = io.open(IMPL, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    header = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    done = 0
    for name, (signature, statement) in BODIES.items():
        pattern = re.compile(r"^void %s\(void\* \w+, int \w+\) \{(.*?)\n\}" % re.escape(name), re.S | re.M)
        match = pattern.search(impl)
        if not match:
            if re.search(r"^void %s\(Order\* order, int value\) \{" % re.escape(name), impl, re.M):
                print("   %-42s already typed" % name)
                continue
            print("   %-42s NOT FOUND in the expected shape" % name)
            continue
        replacement = "void %s(%s) {\n    %s\n}" % (name, signature, statement)
        impl = impl[:match.start()] + replacement + impl[match.end():]
        head = re.compile(r"^void %s\(void\* \w+, int \w+\);" % re.escape(name), re.M)
        if head.search(header):
            header = head.sub("void %s(%s);" % (name, signature), header, count=1)
        print("   %-42s typed as (%s)" % (name, signature))
        done += 1
    if apply:
        io.open(IMPL, "w", encoding="utf-8", newline="\n").write(impl)
        io.open(HEADER, "w", encoding="utf-8", newline="\n").write(header)
        print("%d function(s) written" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
