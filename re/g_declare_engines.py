# -*- coding: utf-8 -*-
"""Declare the other six Engine classes instead of only listing their addresses.

The defect the human found, applied to the header that carries it: engines.hpp names six classes, gives each a vtable and three slot
addresses, and declares only InfiniteEngine. **A constant named kCompositeEngineRun is not a class**, and a reader -- or a commit message
-- can take it for one, which is what happened.

So the six get DECLARATIONS. Their members are not known and are not invented: what is known is that each is an Engine with the same three
slots and the same Run signature, and that is what a declaration can honestly say. Where a body has been read the declaration says what it
does; where it has not, the comment says which address remains unread.

    python g_declare_engines.py
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "engines.hpp")

CLASSES = [
    ("MultiEngine", 0x755050, 0xA3CF00, "not read"),
    ("DelayedEngine", 0x756EC0, 0xA3CF70, "not read"),
    ("NestingEngine", 0x757250, 0xA3CFA0, "not read"),
    ("CompositeEngine", 0x759B70, 0xA3D000,
     "read far enough to establish that it calls NO other engine's Run: it walks a container of 16 byte records and accumulates"),
    ("EquivalentEngine", 0x75BCC0, 0xA3D030, "not read"),
    ("CloudEngine", 0x26A60, 0xA3CED0, "not read"),
]

ANCHOR = "static_assert(kEngineRunSlot == 0x10,"


def main():
    text = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "class MultiEngine" in text:
        print("already declared")
        return 0

    block = [""]
    block.append("// ------------------------------------------------------------------------------------------------")
    block.append("// THE OTHER SIX, DECLARED.")
    block.append("//")
    block.append("// Each is an Engine with the same three slots and the same Run signature, which is everything the RTTI and the call site")
    block.append("// establish. **Members are not invented**: the vtable says how many virtuals a class has and nothing about its data, so a")
    block.append("// declaration here carries what is known and the comment says which body remains unread.")
    block.append("//")
    block.append("// A constant named kCompositeEngineRun is NOT a class, and a header that gives six classes an address and declares none of")
    block.append("// them invites exactly that misreading -- which happened, and is why these exist.")
    for name, run, vtable, note in CLASSES:
        block.append("")
        block.append("/** Engine::%s, Run at 0x%X, vtable 0x%X." % (name, run, vtable))
        block.append(" *")
        block.append(" *  %s." % note.capitalize())
        block.append(" */")
        block.append("class %s : public EngineBase {" % name)
        block.append("public:")
        block.append("    %s() = default;" % name)
        block.append("")
        block.append("    void* run(const void* problem, double timeLimit, void* observer, void* result) override;")
        block.append("};")
    block.append("")

    # keep the constants, they are the addresses the declarations point at
    text = text.replace(ANCHOR, "\n".join(block).lstrip("\n") + "\n\n" + ANCHOR, 1)
    io.open(HEADER, "w", encoding="utf-8", newline="\n").write(text)
    print("declared %d classes in engines.hpp" % len(CLASSES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
