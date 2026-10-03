# -*- coding: utf-8 -*-
"""Type the local-engine setters with `Order*` instead of `void*` plus a carrier, and verify the fields agree.

**THE `void*` IS ERASURE AND IT HID A REAL BUG.** `setMultiTorchCuttingPreference` took two arguments where the module reads three and derived its flag from the
value where `0xF22C`' `setg` reads `r8d` -- **and the erasure is what let that compile**, because a signature that says `void*, int` cannot be checked against an
object whose fields have names and widths.

**THIS IS THE NARROW CASE WHERE NOTHING CAN GO WRONG**: `LocalEngineCarrier`'s three fields and `Order`'s three are the SAME types at the SAME offsets --
`std::uint32_t` at +0x1F8, `std::uint32_t` at +0x1FC, `std::uint8_t` at +0x200 and +0x201 -- so the change is the type and nothing else. **The wider carriers
need their field types reconciled first** (`SolverOptionCarrier::objective` is `std::int32_t` where `Order`'s is the `Objective` enum, and `OptionFlagCarrier`'s
`field44` is `std::uint32_t` where `Order`'s `shear` is `bool`), **and a rename that also changes a width is two changes pretending to be one.**
"""
import io
import re
import sys

ROOT = r"D:\Nesting\nestfab"
IMPL = ROOT + r"\lcns\src\exports_impl.cpp"
HEADER = ROOT + r"\lcns\include\lcns\exports_impl.hpp"
API = ROOT + r"\lcns\src\api_exports.cpp"

# the two implementations, and the wrapper that calls each
FUNCTIONS = [
    ("setLocalMaximumThreads", "Order* order",
     "order->maxThreads = clampMaximumThreads(platformConcurrency(), value);",
     "Order", "order", "value"),
    ("setLocalMaximumIterations", "Order* order",
     "order->maxIterations = static_cast<std::uint32_t>(value);",
     "Order", "order", "value"),
]


def main(apply):
    impl = io.open(IMPL, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    header = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    api = io.open(API, encoding="utf-8", newline="").read().replace("\r\n", "\n")

    for name, signature, body, _t, _p, _v in FUNCTIONS:
        # the implementation
        pattern = re.compile(r"^void %s\(void\* object, int value\) \{(.*?)\n\}" % re.escape(name), re.S | re.M)
        match = pattern.search(impl)
        if not match:
            print("   %-30s implementation not found in the expected shape" % name)
            continue
        comment_lines = [line for line in match.group(1).split("\n") if line.strip().startswith("//")]
        replacement = ("void %s(%s) {\n%s    %s\n}"
                       % (name, signature, ("\n".join(comment_lines) + "\n") if comment_lines else "", body))
        impl = impl[:match.start()] + replacement + impl[match.end():]
        # and the declaration
        pattern = re.compile(r"^void %s\(void\* object, int value\);" % re.escape(name), re.M)
        match = pattern.search(header)
        if match:
            header = header[:match.start()] + "void %s(%s);" % (name, signature) + header[match.end():]
        # and every wrapper that calls it
        api = re.sub(r"impl::%s\(static_cast<void\*>\((\w+)\), (\w+)\)" % re.escape(name),
                     r"impl::%s(\1, \2)" % name, api)
        print("   %-30s typed as (%s)" % (name, signature))

    if apply:
        io.open(IMPL, "w", encoding="utf-8", newline="\n").write(impl)
        io.open(HEADER, "w", encoding="utf-8", newline="\n").write(header)
        io.open(API, "w", encoding="utf-8", newline="\n").write(api)
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
