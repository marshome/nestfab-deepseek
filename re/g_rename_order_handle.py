# -*- coding: utf-8 -*-
"""Rename the opaque handle `Order` to `OrderHandle`, because `Order` is now the real class.

**`lcns/api.hpp` SAYS `LCNS_OPAQUE(Order)`, WHICH IS `struct Order_t; using Order = Order_t*`.** And `lcns/model.hpp` declares `struct Order`, the module's object
with named fields. **Two declarations of one name, and the linker showed it:**

    defined:    lcns::dll::exports::impl::setLocalMaximumThreads(lcns::Order*, int)
    referenced: lcns::dll::exports::impl::setLocalMaximumThreads(lcns::dll::Order_t**, int)

**THE HANDLE KEEPS ITS MEANING AND LOSES ITS NAME**: `using OrderHandle = Order_t*` is the same type through the C ABI, and the wrappers whose first argument is
the order now say `OrderHandle` so that the word `Order` unambiguously means the class.

**AND ONLY `Order` IS RENAMED.** `Part`, `Sheet`, `Nesting`, `NestedPart` and `Solution` are used as RETURN types with `return 0` and `return nullptr` in the
generated stubs -- so making those into real classes is a change to the generated table's return values and not a rename, **and a rename that also changes what a
function returns is two changes pretending to be one.**
"""
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:\Nesting\nestfab"
HPP = os.path.join(ROOT, "lcns", "include", "lcns", "api.hpp")
CPP = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")


def main(apply):
    hpp = io.open(HPP, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    cpp = io.open(CPP, encoding="utf-8", newline="").read().replace("\r\n", "\n")

    if "LCNS_OPAQUE(Order);" in hpp:
        hpp = hpp.replace(
            "LCNS_OPAQUE(Order);        // LaunchingOrder   (NewLaunchingOrder)",
            "// **`Order` IS THE REAL CLASS IN lcns/model.hpp, SO THE HANDLE IS NAMED `OrderHandle`.** A handle that shares its name with the class it points at is\n"
            "// two declarations of one name: `using Order = Order_t*` beside `struct Order`, which makes a signature saying `Order*` mean `Order_t**`.\n"
            "struct Order_t;\n"
            "using OrderHandle = Order_t*;   // LaunchingOrder   (NewLaunchingOrder)", 1)
        print("   api.hpp: the handle is now OrderHandle")

    # **THE SUBSTITUTION MUST NOT TOUCH COMMENTS OR STRINGS.** The generated file is mostly comments, and the plain `\bOrder\b` replacement rewrote the prose --
    # including the sentence explaining the rename. **A rename that edits its own explanation is a rename that cannot be read afterwards.** So the comments and
    # strings are lifted out, the code is renamed, and they are put back.
    literals = []

    def stash(match):
        literals.append(match.group(0))
        return "\x00%d\x00" % (len(literals) - 1)

    cpp = re.sub(r'//[^\n]*|/\*.*?\*/|"(?:[^"\\]|\\.)*"', stash, cpp, flags=re.S)
    before = len(re.findall(r"\bOrder\b", cpp))
    cpp = re.sub(r"\bOrder\b(?!\w)", "OrderHandle", cpp)
    after = len(re.findall(r"\bOrderHandle\b", cpp))
    cpp = re.sub(r"\x00(\d+)\x00", lambda m: literals[int(m.group(1))], cpp)
    print("   api_exports.cpp: %d mention(s) in CODE before, %d OrderHandle now" % (before, after))

    if apply:
        io.open(HPP, "w", encoding="utf-8", newline="\n").write(hpp)
        io.open(CPP, "w", encoding="utf-8", newline="\n").write(cpp)
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
