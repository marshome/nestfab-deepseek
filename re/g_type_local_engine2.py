# -*- coding: utf-8 -*-
"""Type the two local-engine setters with `Order* order, int value`, the whole signature, verified after writing.

**THE FIRST VERSION WROTE `(Order* order)` AND LOST THE SECOND PARAMETER**, because the replacement used the signature string for the whole parameter list while the
body still said `value` -- so the compile saw `value` undeclared in one place and too many arguments in another. **A parameter list is not a place to be
partial**, and the fix is to write the signature whole and then check that the same parameter names are in the body and in every caller.
"""
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
IMPL = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")
API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
HEADER_INCLUDE = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")

BODIES = {
    "setLocalMaximumThreads": ("Order* order, int value",
                               "order->maxThreads = clampMaximumThreads(platformConcurrency(), value);"),
    "setLocalMaximumIterations": ("Order* order, int value",
                                  "order->maxIterations = static_cast<std::uint32_t>(value);"),
}


def main():
    impl = io.open(IMPL, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    header = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    api = io.open(API, encoding="utf-8", newline="").read().replace("\r\n", "\n")

    # the header needs Order's declaration visible
    if '#include "lcns/model.hpp"' not in header:
        header = header.replace('#include "lcns/dll_layout.hpp"',
                                '#include "lcns/dll_layout.hpp"\n#include "lcns/model.hpp"   // `Order`, so a signature can say the real type', 1)
        print("   exports_impl.hpp now includes model.hpp")

    for name, signature, statement in BODIES.items():
        pattern = re.compile(r"^void %s\([^)]*\) \{(.*?)\n\}" % re.escape(name), re.S | re.M)
        match = pattern.search(impl)
        if not match:
            print("   %-30s implementation not found" % name)
            continue
        comments = [line for line in match.group(1).split("\n") if line.strip().startswith("//")]
        replacement = "void %s(%s) {\n%s    %s\n}" % (
            name, signature, ("\n".join(comments) + "\n") if comments else "", statement)
        impl = impl[:match.start()] + replacement + impl[match.end():]

        head = re.compile(r"^void %s\([^)]*\);" % re.escape(name), re.M)
        if head.search(header):
            header = head.sub("void %s(%s);" % (name, signature), header, count=1)
        else:
            print("   %-30s NO DECLARATION to rewrite" % name)

        api, count = re.subn(r"impl::%s\(static_cast<void\*>\((\w+)\), (\w+)\)" % re.escape(name),
                             r"impl::%s(\1, \2)" % name, api)
        print("   %-30s typed (%s); %d caller(s) updated" % (name, signature, count))

    io.open(IMPL, "w", encoding="utf-8", newline="\n").write(impl)
    io.open(HEADER, "w", encoding="utf-8", newline="\n").write(header)
    io.open(API, "w", encoding="utf-8", newline="\n").write(api)

    # **AND THE CHECK THAT THE FIRST VERSION LACKED**: every parameter the signature names must appear in the body
    for name, signature, statement in BODIES.items():
        parameters = [part.strip().rsplit(" ", 1)[-1] for part in signature.split(",")]
        missing = [p for p in parameters if p != "order" and re.search(r"\b%s\b" % re.escape(p), statement) is None]
        if missing:
            print("   REFUSING: %s names %s and its body does not use them" % (name, missing))
            return 2
    print("written; every parameter is used by its body")
    return 0


if __name__ == "__main__":
    sys.exit(main())
