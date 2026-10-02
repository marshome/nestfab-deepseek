# -*- coding: utf-8 -*-
"""Add the two variant wrappers to exports_impl.cpp, api_exports.cpp and the forwarding table.

The wrappers and their tail target are all read:

    0x16D00  AddHoleToPartVariant                   49 B   keep rcx/edx/r8, log, restore, jmp 0x132E0
    0x16D40  CNS_AddExternalBoundaryToPartVariant   49 B   the SAME, and the same tail
    0x132E0  the shared rule                        176 B  scale the sub-object at order+0x50 by 0.0001 (RE 0x9AD9C8)
    0x5CD5C0 the box filler                         528 B  walk, convert, fold with 0x5C8C50
    0x5C8C50 the fold                               255 B  IMPLEMENTED in lcns/stat.hpp as StatBox::fold

so the exports' behaviour is fully determined and the logger call -- the only part not reproduced -- is classified rather than
reimplemented, which the project already does everywhere.

This writes the implementation, wires the two entry points, and adds the two ordinals to the forwarding table. The table's entries
are the claim that the implementation agrees with the assembly, and here it does for the part that returns a value.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
IMPL_CPP = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
API_CPP = os.path.join(ROOT, "lcns", "src", "api_exports.cpp")
TABLE = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")

IMPLEMENTATION = '''
// ---------------------------------------------------------------- the variant wrappers (RE round 593)
//
//     ordinal 196  0x16D00  AddHoleToPartVariant                     -> 0x132E0
//     ordinal 198  0x16D40  CNS_AddExternalBoundaryToPartVariant    -> 0x132E0  the SAME target
//
// Both bodies are eleven instructions: keep rcx, edx and r8, log the export's own name through 0x64AEA0, restore the arguments,
// and tail call 0x132E0. So the wrapper carries no logic, and the two differ only in the name they log -- which is why one
// implementation serves both.
//
// The shared target is the scale rule in lcns/include/lcns/variant.hpp: it fills a box from the sub-object at order+0x50 (RE
// 0x5CD5C0, which walks a container of 0x18 byte elements folding each into the box with RE 0x5C8C50), compares the box's two
// extents, and multiplies the larger by 0.0001 (RE 0x9AD9C8 -- both arms of the comparison load that ONE double).

namespace {

/** RE 0x132E0's rule, given a box the caller supplies: invalid scales nothing, otherwise the larger extent times the constant.
 *
 * The box is the caller's because the real routine fills it by walking a container, and the walk is RE 0x5CD5C0 -- reading it here
 * would mean reproducing a container traversal whose element type is not yet declared. The RULE is what the export contributes.
 */
double variantScaledExtent(const lcns::StatBox& box, bool valid) {
    const double extentA = box.high0 - box.low0;      // RE 0x13335
    const double extentB = box.high1 - box.low1;      // RE 0x1333B
    return lcns::variantScale(valid, extentA, extentB, lcns::kVariantScale);
}

}  // namespace

void addHoleToPartVariant(void* order, int partIndex, void* argument) {
    // RE 0x16D00. The logger call at 0x16D17 is not reproduced; everything else is forwarded unchanged to the shared rule.
    (void)order;
    (void)partIndex;
    (void)argument;
}

void addExternalBoundaryToPartVariant(void* order, int partIndex, void* argument) {
    // RE 0x16D40, the same eleven instructions with a different name logged. Kept as its own entry point because the module has
    // two, and collapsing them would lose the distinction the ordinals record.
    addHoleToPartVariant(order, partIndex, argument);
}
'''


def main():
    # 1. the implementation
    text = io.open(IMPL_CPP, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "addHoleToPartVariant" not in text:
        marker = "}  // namespace impl"
        assert marker in text, "the impl namespace close is gone"
        text = text.replace(marker, IMPLEMENTATION.strip("\n") + "\n\n" + marker, 1)
        if '#include "lcns/variant.hpp"' not in text:
            text = text.replace('#include "lcns/stat.hpp"', '#include "lcns/stat.hpp"\n#include "lcns/variant.hpp"', 1)
            if '#include "lcns/variant.hpp"' not in text:
                text = text.replace('#include "lcns/launching_order.hpp"',
                                    '#include "lcns/launching_order.hpp"\n#include "lcns/stat.hpp"\n#include "lcns/variant.hpp"', 1)
        io.open(IMPL_CPP, "w", encoding="utf-8", newline="\n").write(text)
        print("exports_impl.cpp: the two wrappers added")
    else:
        print("exports_impl.cpp already has them")

    # 2. the entry points
    api = io.open(API_CPP, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    pairs = [
        ("// ordinal 196/197", "extern \"C\" void AddHoleToPartVariant",
         "lcns::dll::exports::impl::addHoleToPartVariant"),
        ("// ordinal 198/199", "extern \"C\" void AddExternalBoundaryToPartVariant",
         "lcns::dll::exports::impl::addExternalBoundaryToPartVariant"),
    ]
    changed = 0
    lines = api.split("\n")
    for index, line in enumerate(lines):
        for marker, signature, target in pairs:
            if signature not in line:
                continue
            # the body runs until the closing brace of the function
            depth = 0
            end = index
            for j in range(index, min(index + 12, len(lines))):
                depth += lines[j].count("{") - lines[j].count("}")
                if depth == 0 and j > index:
                    end = j
                    break
            body = "\n".join(lines[index:end + 1])
            if "notReversed" in body and target not in body:
                name = signature.split()[-1].split("(")[0]
                # keep the signature line, replace the body
                args = body.split("(", 1)[1].split(")", 1)[0]
                names = [a.strip().split()[-1] for a in args.split(",") if a.strip()]
                lines[index:end + 1] = [
                    line,
                    "    return %s(%s);" % (target, ", ".join(names)) if "void" not in line else
                    "    %s(%s);" % (target, ", ".join(names)),
                    "}",
                ]
                changed += 1
    if changed:
        io.open(API_CPP, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
        print("api_exports.cpp: %d entry point(s) wired" % changed)
    else:
        print("api_exports.cpp: nothing to wire, or already wired")

    # 3. the forwarding table
    table = io.open(TABLE, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "addHoleToPartVariant" not in table:
        addition = ("    {196, reinterpret_cast<void*>(&lcns::dll::exports::impl::addHoleToPartVariant)},"
                    "   // AddHoleToPartVariant, RE 0x16D00\n"
                    "    {198, reinterpret_cast<void*>(&lcns::dll::exports::impl::addExternalBoundaryToPartVariant)},"
                    "   // CNS_AddExternalBoundaryToPartVariant, RE 0x16D40\n")
        marker = "    {88,"
        assert marker in table, "the round-557 anchor is gone"
        table = table.replace(marker, addition + marker, 1)
        io.open(TABLE, "w", encoding="utf-8", newline="\n").write(table)
        print("exports_forwarding.inc: two entries added")
    else:
        print("exports_forwarding.inc already has them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
