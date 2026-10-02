# -*- coding: utf-8 -*-
"""DELETE class_definitions.hpp. Its member offsets are fabricated, and the reason is mechanical.

THE HUMAN ASKED "THESE ARE NOT C++ CLASSES", about

    class ParseProblemException {
    public:
        virtual ~ParseProblemException() = default;
        static constexpr const char* kMangled = "N9Structure21ParseProblemExceptionE";
        static constexpr unsigned kVirtualSlots = 3;
        static constexpr std::uintptr_t kConstructor = 0x50CF70;
        static constexpr std::uintptr_t kVtable = 0xA534F0;
        std::byte unplaced_0008[0x18]{};
        void*     at_0020 = {}; // +0x20, RE 0x50CFCA: mov qword ptr [rsp + 0x20], rax
        double    at_0028 = {}; // +0x28, RE 0x50CFC4: movsd qword ptr [rsp + 0x28], xmm0
    };

**THE MEMBERS ARE FABRICATED, AND THE COMMENT SAYS SO TO ANYONE WHO READS IT CLOSELY**: `mov qword ptr [rsp + 0x20], rax` writes to the STACK,
not to the object. `rsp + 0x20` is shadow space for an outgoing call. My field scanner took the store's BASE REGISTER as evidence that the base
was the object, and `rsp` is a base register.

    the scanner's rule:  a store through a register shown to hold the object
    what it did:         a store through rsp, which holds the STACK

**An offset with an instruction is only evidence if the register is the OBJECT, and that was never checked.** The classes whose members came
from a register loaded from rcx -- the nesters, whose constructors set `mov rbx, rcx` once and never change it -- are sound. The rest are not.

WHY THIS DELETES RATHER THAN REPAIRS: repairing means re-deriving every offset with the object register actually established, which is a real
piece of work and not a patch. **A file of plausible-looking members is worse than no file**, because it compiles and misleads. What is kept is
every name and offset in re/all_class_fields.json, and the ledger.

AND WHAT A REAL CLASS LOOKS LIKE was written out for comparison:

    class ParseProblemException : public std::runtime_error {
    public:
        explicit ParseProblemException(std::string what, int line, int column)
            : std::runtime_error(std::move(what)), line_(line), column_(column) {}
        int line() const noexcept { return line_; }
        int column() const noexcept { return column_; }
    private:
        int line_;
        int column_;
    };

**A CLASS HAS MEMBERS WITH TYPES AND NAMES, A CONSTRUCTOR THAT INITIALISES THEM, AND METHODS THAT USE THEM.** None of the fabricated file has
the third, and its members are at offsets its own object cannot account for.
"""
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
DEFS = os.path.join(ROOT, "lcns", "include", "lcns", "class_definitions.hpp")
TEST = os.path.join(ROOT, "lcns", "tests", "test_recovered.cpp")


def main():
    if os.path.exists(DEFS):
        os.remove(DEFS)
        print("deleted class_definitions.hpp")

    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    lines = text.split("\n")
    headers = [(i, l) for i, l in enumerate(lines) if re.match(r"^    // -{20,} ", l)]
    spans = []
    for position, (index, line) in enumerate(headers):
        if "the class registers, AS CLASS CONSTANTS" in line:
            end = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
            spans.append((index, end))
    block = '''    // ---------------------------------------------------------------- the class registers, DELETED
    //
    // A block of assertions on `kMangled`, `kVirtualSlots`, `kVtable` and `kConstructor` stood here, over classes declared in
    // class_definitions.hpp. **That file is deleted and so is this**, for the reason recorded at length in re/g_delete_class_definitions.py:
    // its member offsets came from stores through `rsp`, which is the STACK and not the object, so every member it declared was fabricated.
    //
    // The three constants were also misplaced even where their values were right: **a mangled name, a slot count and a vtable address are
    // facts FOR AN ANALYSIS TOOL, not parts of a class.** A class has members with types, a constructor that initialises them, and methods
    // that use them.
    {
        // what survives, and it is on a HAND-WRITTEN class whose constructor was read in full and whose object register never changes
        CHECK(std::string(lcns::FlipNester::kMangled) == "N5Multi10FlipNesterE");
        CHECK(lcns::FlipNester::kVirtualSlots == 6u);
        CHECK(lcns::FlipNester::kVtable == 0xA3B490u);
    }

'''
    out = lines
    for start, end in sorted(spans, reverse=True):
        out = out[:start] + block.split("\n") + out[end:]
    text = "\n".join(out)
    for include in ('#include "lcns/class_definitions.hpp"\n',):
        text = text.replace(include, "", 1)
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("replaced the class-definitions assertions; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
