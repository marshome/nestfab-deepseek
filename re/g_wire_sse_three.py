# -*- coding: utf-8 -*-
"""Wire the three refusals that were the PROBE's fault: SetShearGap, SetMarkMode and sub_0B000.

**ALL THREE HAVE AN IMPLEMENTATION THAT MATCHES THE INSTRUCTIONS, AND ALL THREE WERE REFUSED BECAUSE THE PROBE READ ONLY THE INTEGER REGISTERS.**

    SetShearGap   ord 212, 0x1A600      reads rcx and xmm1        -> (void* options, double gap)
    SetMarkMode   ord 246, 0x188D0      reads rcx, edx, xmm2, xmm3 -> (void* order, int flag, double, double)
    sub_0B000     ord 286, 0xB000       reads rcx, edx, xmm2      -> (void* object, int flag, double value)

**AND EACH SIGNATURE IS READ FROM THE FUNCTION'S OWN MOVES** rather than from the count: `0x188F0 movapd xmm7, xmm2` proves xmm2 is an input, and `0xB002 movsd
qword [rcx + 0x100], xmm2` proves xmm2 is the double that gets stored. **The count was only ever a filter; the moves are the evidence.**
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
API = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")

WIRINGS = [
    ("SetShearGap", "void", "Order* order, double gap",
     "lcns::dll::exports::impl::setShearGap(static_cast<void*>(order), gap);",
     "**THE MODULE READS ONE INTEGER REGISTER AND ONE XMM, SO THE FIRST PARAMETER IS A POINTER AND THE SECOND IS A DOUBLE.** The inferred table said "
     "`(Order, double)`, which is right about the second and wrong about the first."),
    ("SetMarkMode", "void", "Order* order, int flag, double first, double second",
     "lcns::dll::exports::impl::setMarkMode_188D0(static_cast<void*>(order), flag, first, second);",
     "**FOUR ARGUMENTS AND THE PROBE SAID TWO**, because 0x188F0 `movapd xmm7, xmm2` and 0x188F4 `movapd xmm6, xmm3` put two DOUBLES in xmm2 and xmm3 and a "
     "probe that reads only rcx/rdx/r8/r9 cannot see them. `setMarkMode_188D0(void*, int, double, double)` matches the four moves exactly."),
    ("sub_0B000", "void", "Order* order, int flag, double value",
     "lcns::dll::exports::impl::setDoubleAndFlag(static_cast<void*>(order), flag, value);",
     "**THE BODY IS THREE INSTRUCTIONS AND USES ALL THREE ARGUMENTS**: `0xB000 test edx, edx`, `0xB002 movsd qword [rcx + 0x100], xmm2` and `0xB00A setne byte "
     "[rcx + 0xf9]`. So the flag is `edx > 0`, the double is `xmm2` and the object is `rcx` -- and `setDoubleAndFlag(void*, int, double)` matches."),
]


def main():
    api = io.open(API, encoding="utf-8", errors="replace").read()
    done = 0
    for name, return_type, parameters, call, note in WIRINGS:
        pattern = re.compile(r'extern\s+"C"\s+[^;{]*?\b%s\s*\(([^)]*)\)\s*\{(.*?)\n\}' % re.escape(name), re.S)
        match = pattern.search(api)
        if not match:
            print("   %-20s no wrapper found" % name)
            continue
        if "impl::" in match.group(2):
            print("   %-20s already dispatches" % name)
            continue
        replacement = ('extern "C" %s %s(%s) {\n    // %s\n    %s\n}'
                       % (return_type, name, parameters, note, call))
        api = api[:match.start()] + replacement + api[match.end():]
        api = re.sub(r'(\{"%s",\s*\d+,\s*\d+,\s*0x[0-9A-Fa-f]+u,\s*\d+u,\s*)Status::NotReversed,\s*""'
                     % re.escape(name), r'\1Status::Forwarded, "// wired after the SSE arguments were counted"', api, count=1)
        print("   %-20s wired" % name)
        done += 1

    if done:
        io.open(API, "w", encoding="utf-8", newline="\n").write(api)
        print("%d wrapper(s) written" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main())
