# -*- coding: utf-8 -*-
"""Rewrite lcns/launching_order.hpp with the fields that HAVE names named, and only the rest left unnamed.

Round 538. slot000 is a placeholder and it was being used for fields that already have a name from evidence. This rebuilds
the header from two sources and names everything they cover:

  * 0x14620 NewLaunchingOrder writes 96 fields and fixes the size at 0x2C0, so it gives every offset and its width;
  * eight exports name the fields they set, from round 537: SetAutomaticStop +0x240, SetCommonCutSafetyPreference
    +0x068/+0x06C, SetCommonCutCuttingPreference +0x088/+0x08C, SetMultiTorchCuttingPreference +0x098/+0x09C/+0x0A0,
    SetMarkMode +0x0E0/+0x0E8/+0x0F0, SetSpecificSheetOrigin +0x124/+0x128, SetSpecificSheetObjective +0x12C/+0x130,
    SetOrigin +0x00C, CNS_SetMultiplicityPreference +0x010;
  * plus what the accessor witnesses and an earlier round's hand reading named: GetPartUserStringEx +0x1B8, the empty slot
    marker at +0x110/+0x118/+0x120, and Multi::RowNester's common-cut parameters at +0x1A0/+0x1A8/+0x1B0/+0x1B8/+0x1C0.

Every other field keeps an offset-derived name rather than a meaning-derived one, and the header says why in one line: the
module gives those fields no name anywhere this project can read. A name invented for them would be the mistake this file
exists to avoid.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib import disasm, load_prof  # noqa: E402

ROOT = os.path.dirname(HERE)
PATH = os.path.join(ROOT, "lcns", "include", "lcns", "launching_order.hpp")
CTOR = 0x14620
STORE = re.compile(r"^(byte|word|dword|qword|xmmword) ptr \[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\], (.+)$")
WIDTH = {"byte": 1, "word": 2, "dword": 4, "qword": 8, "xmmword": 16}

# The names the module gives, with the evidence. Anything not in here is unnamed on purpose.
NAMES = {
    0x00C: ("origin", "RE 0xD119, SetOrigin (86)"),
    0x010: ("multiplicityPreference", "RE 0xD26A, CNS_SetMultiplicityPreference (128), a double"),
    0x068: ("commonCutSafetyPreferenceGiven", "RE 0xEA09, SetCommonCutSafetyPreference (150), byte = 1"),
    0x06C: ("commonCutSafetyPreference", "RE 0xEA0D, SetCommonCutSafetyPreference (150)"),
    0x088: ("commonCutCuttingPreferenceGiven", "RE 0xED59, SetCommonCutCuttingPreference (154), byte = 1"),
    0x08C: ("commonCutCuttingPreference", "RE 0xED60, SetCommonCutCuttingPreference (154)"),
    0x098: ("multiTorchCuttingPreferenceGiven", "RE 0xF225, SetMultiTorchCuttingPreference (176), byte = 1"),
    0x09C: ("multiTorchCuttingPreference", "RE 0xF233, SetMultiTorchCuttingPreference (176)"),
    0x0A0: ("multiTorchCuttingPreferencePositive", "RE 0xF22C, setg on the same argument"),
    0x0E0: ("markModeGiven", "RE 0x18A09, SetMarkMode (246), setne on the flag"),
    0x0E8: ("markModeFirst", "RE 0x189FA, SetMarkMode (246), the double in xmm2"),
    0x0F0: ("markModeSecond", "RE 0x18A10, SetMarkMode (246), the double in xmm3"),
    0x110: ("emptySlotMarker0", "RE 0x14793, the constant 0x3FFFFFFF"),
    0x118: ("emptySlotMarker1", "RE 0x1479E, the constant 0x3FFFFFFF"),
    0x120: ("emptySlotMarker2", "RE 0x147A9, the constant 0x3FFFFFFF"),
    0x124: ("specificSheetOriginGiven", "RE 0x13F02, SetSpecificSheetOrigin (298), byte = 1"),
    0x128: ("specificSheetOrigin", "RE 0x13F09, SetSpecificSheetOrigin (298)"),
    0x12C: ("specificSheetObjectiveGiven", "RE 0x140B2, SetSpecificSheetObjective (300), byte = 1"),
    0x130: ("specificSheetObjective", "RE 0x140B9, SetSpecificSheetObjective (300)"),
    0x170: ("pipeMode", "RE 0xFCF0 SetPipeMode, read by 0x4FC2F0 / 0x4FC300"),
    0x1A0: ("commonCutParameterA", "RE 0x3C3F0 SetCommonCutParameters, read by 0x4FC3C0"),
    0x1A8: ("commonCutParameterB", "RE 0x3C3F0"),
    0x1B0: ("commonCutParameterC", "RE 0x3C3F0"),
    0x1B8: ("userString", "RE 0x14855 and GetPartUserStringEx (55)"),
    0x1C0: ("commonCutParameterE", "RE 0x3C3F0"),
    0x240: ("automaticStop", "RE 0xE0D9, SetAutomaticStop (140); read by 0x22A20 at RE 0x22BC1"),
    0x288: ("estimateLocalComputation", "RE 0x3383, LaunchEstimateLocalComputation (216)"),
    0x2A8: ("nodeList", "RE 0x5007C0 through the order dereference"),
}

TYPES = {
    1: "std::uint8_t", 2: "std::uint16_t", 4: "std::uint32_t", 8: "std::uint64_t", 16: "unsigned char[16]",
}

# The fields whose setter stores a DOUBLE, so the declaration must be `double` and not a 64-bit integer: `movsd` moves a
# floating value, and declaring the slot as an integer makes the compiler insert a conversion. RE 0xD255, RE 0x189FA and
# RE 0x18A10 are all `movsd`, and the failing test was the compiler doing exactly that conversion.
DOUBLE_FIELDS = {0x010, 0x0E8, 0x0F0}
TYPE_DOUBLE = "double"

# The width of a field the constructor does not write, taken from the store the NAME came from. RE 0xD255 stores a double at
# +0x10, RE 0x13F09 and RE 0x140B9 store a dword, and everything else named is a byte flag.
NAMED_WIDTHS = {
    0x010: 8,    # RE 0xD255, movsd
    0x0E8: 8,    # RE 0x189FA, movsd
    0x0F0: 8,    # RE 0x18A10, movsd
    0x124: 1,    # RE 0x13F02, mov byte = 1
    0x128: 4,    # RE 0x13F09, mov dword
    0x12C: 1,    # RE 0x140B2
    0x130: 4,    # RE 0x140B9, mov dword
    0x068: 1, 0x06C: 4, 0x088: 1, 0x08C: 4, 0x098: 1, 0x09C: 4, 0x0A0: 1, 0x0E0: 1,
    0x170: 1, 0x1A0: 8, 0x1A8: 8, 0x1B0: 8, 0x1B8: 8, 0x1C0: 8, 0x240: 4, 0x288: 4, 0x2A8: 8,
    0x00C: 4, 0x110: 8, 0x118: 8, 0x120: 8,
}


def fields():
    profile = load_prof()
    size = (profile.get(CTOR) or {}).get("size") or 0
    body = [i for i in disasm(CTOR) if i.address < CTOR + size]
    written = {}
    for ins in body:
        m = STORE.match(ins.op_str)
        if not m or m.group(2) not in ("rax", "rbx"):
            continue
        offset = int(m.group(3), 16) if m.group(3) else 0
        width = WIDTH[m.group(1)]
        written[offset] = max(written.get(offset, 0), width)
    return written


def main():
    written = fields()
    # One pass over the offsets: where a name exists, emit the field; where the constructor writes a value, emit it with an
    # offset-derived name; where neither, collect the gap into ONE unnamed run. The first version emitted a single byte per
    # unnamed offset, which is how `specificSheetOriginGiven` at +0x124 ended up declared as `unsigned char[0x128]` -- the
    # name was there in the table but the byte-by-byte walk never reached it.
    named_offsets = sorted(set(list(NAMES) + list(written)))
    lines = []
    used = set()
    cursor = 0
    for index, offset in enumerate(named_offsets):
        following = named_offsets[index + 1] if index + 1 < len(named_offsets) else 0x2C0
        # a gap before this offset is its own field, so the layout is exact and the size assertion holds
        if offset > cursor:
            lines.append("    unsigned char unnamed%03X[0x%X];   // +0x%03X..+0x%03X, not written by RE 0x14620"
                         % (cursor, offset - cursor, cursor, offset - 1))
            cursor = offset
        if offset < cursor:
            continue
        available = following - offset
        width = written.get(offset, 0)
        name, evidence = NAMES.get(offset, ("", ""))
        if name and offset in NAMED_WIDTHS:
            # For a NAMED field the store the name came from is the authority, not the constructor: RE 0x140B9 is
            # `mov dword ptr [rdi+0x130], ebp` while the constructor writes eight bytes there, and the setter is what the
            # field's meaning is read from.
            width = NAMED_WIDTHS[offset]
        elif width == 0:
            width = NAMED_WIDTHS.get(offset, min(available, 4))
        # A field may not run into the next named one: the boundary between them is what makes the layout exact. The second
        # version of this loop advanced a cursor by each field's width, so a named field that began inside a preceding gap
        # was reported as an overlap and silently dropped -- specificSheetOriginGiven at +0x124 went missing that way while
        # the run still printed "26 of 96 named".
        if width > available:
            width = available
        if width <= 0:
            continue
        if not name:
            name = "unnamed%03X" % offset
        if name in used:
            name = "%s_%03X" % (name, offset)
        used.add(name)
        declaration = TYPE_DOUBLE if offset in DOUBLE_FIELDS else TYPES.get(width, "unsigned char")
        lines.append("    %-20s %s;   // +0x%03X  %s"
                     % (declaration, name, offset, evidence or "written by RE 0x14620"))
        cursor = offset + width
    if cursor < 0x2C0:
        lines.append("    unsigned char unnamed%03X[0x%X];   // +0x%03X..+0x2BF, not written by RE 0x14620"
                     % (cursor, 0x2C0 - cursor, cursor))

    header = """// lcns/include/lcns/launching_order.hpp -- the launch order's layout, read out of its constructor and its setters.
//
// The size and every offset come from RE 0x14620 NewLaunchingOrder, which allocates 0x2C0 bytes through operator new at
// 0x998500 and then writes 96 fields, the largest at +0x2B8 and nothing above 0x2C0. The names come from the exports that
// set the fields and from the accessors that read them, each carrying the store address that establishes it.
//
// A field with a NAME here is one the module itself names, and the comment says where: eight exports set fields and their
// own names are the field names (SetAutomaticStop sets +0x240, SetMarkMode sets +0xE8 and +0xF0, and so on), GetPartUserStringEx
// reads +0x1B8, and an earlier round read the five common-cut parameters that Multi::RowNester's core reads.
//
// A field with an OFFSET-DERIVED name (unnamedXXX) is one the module never names anywhere this project can read. It is
// spelled that way on purpose: inventing a meaning for it would be the mistake this file exists to prevent, and the
// serialiser channel that could name more of them is located but not yet paired (see re/LAUNCH_LOCAL_COMPUTATION.md).
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {
namespace dll {

/** The launch order, 0x2C0 bytes. RE 0x14636: mov ecx, 0x2C0 ; call operator new. */
struct LaunchingOrderLayout {
    /** The empty-slot marker the constructor writes to +0x110, +0x118 and +0x120: the low 30 bits set. */
    static constexpr std::uint32_t kEmptySlotMarker = 0x3FFFFFFFu;

""" + "\n".join(lines) + """
};

static_assert(sizeof(LaunchingOrderLayout) == 0x2C0,
              "RE 0x14636: NewLaunchingOrder allocates 0x2C0 bytes and its field writes stop at +0x2B8");

// The offsets a reader of this objective needs, asserted so a later edit cannot move them silently.
static_assert(offsetof(LaunchingOrderLayout, userString) == 0x1B8, "RE 0x14855, GetPartUserStringEx reads it");
static_assert(offsetof(LaunchingOrderLayout, automaticStop) == 0x240, "RE 0xE0D9 and RE 0x22BC1");
static_assert(offsetof(LaunchingOrderLayout, estimateLocalComputation) == 0x288, "RE 0x3383");
static_assert(offsetof(LaunchingOrderLayout, emptySlotMarker0) == 0x110, "RE 0x14793");
static_assert(offsetof(LaunchingOrderLayout, markModeFirst) == 0x0E8, "RE 0x189FA");
static_assert(offsetof(LaunchingOrderLayout, nodeList) == 0x2A8, "RE 0x5007C0");

}  // namespace dll
}  // namespace lcns
"""
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(header)
    named = sum(1 for o in written if o in NAMES)
    print("wrote %s: %d fields, %d of them named from the module's own evidence"
          % (PATH, len(written), named))
    return 0


if __name__ == "__main__":
    sys.exit(main())
