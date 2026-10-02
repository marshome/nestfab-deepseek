# -*- coding: utf-8 -*-
"""Append the current status to re/LAUNCH_LOCAL_COMPUTATION.md: what the reader has, and what is left."""
import io

PATH = r"D:\Nesting\nestfab\re\LAUNCH_LOCAL_COMPUTATION.md"

ADD = """

## Where the reader is, and what is implemented (rounds 534 to 536)

**The object is the launch order, 0x2C0 bytes**, and its layout is C++ now: `lcns/include/lcns/launching_order.hpp`, read out
of `0x14620 NewLaunchingOrder`, which allocates 0x2C0 through operator new and writes 96 fields, the largest at +0x2B8.
`re/g_ctor_fields.py 0x14620` prints them all. This is the type `0x2AB0` receives, the type `0x5007C0` destroys, and the type
`0x2AB0` reads its mode from at +0x240.

**The node is 0x48 bytes and IS implemented**: `lcns/include/lcns/cns_node.hpp` holds `0x9302C0` (the copy) and `0x9308C0`
(the release), with the ownership rule the instructions gave -- a string is owned exactly when its pointer is not the node's
own +0x30. `test_recovered.cpp` runs both halves of that rule, an inline string and an outside string, because a release that
frees an inline buffer is the failure the rule exists to prevent.

**The field names have a stated bar**: two independent single-offset accessors must agree on the offset before a name is
used. Six names exist for this object and two clear the bar (+0x10 and +0x50, and both of those belong to the SOLUTION, whose
layout coincides with the order's at those two offsets); the other four carry their single witness in the header. Everything
else keeps slotXXX with the reason written above it.

**The serialisers are located**: `..\\structure\\text_io.cpp` holds the JSON vocabulary -- ToJson (0x50DB70) writes valid,
version, number_of_nested_parts, nestings, sheet_id, multiplicity, common_cut_evaluation, multitorch_infos, number_of_groups,
fill_ratio, min_x, min_y; LoadSheet (0x5091B0) reads geometry, quantity, dimension_x, dimension_y, left_gap, right_gap,
bottom_gap, top_gap, defect_gap; LoadCommonCutEvaluation (0x509A40) reads common_cut, left, right, left_index, right_index,
valid, linked, number_of_common_cut, common_cut_length, regarding_length, segments. Pairing a key to its offset needs the
value flow (key -> the accessor -> the JSON constructor argument), not the nearest accessor, and `re/g_json_fields.py` shows
why: several accessor calls follow each key and the wrong pairing is invisible.

What that leaves in the closure: `0x2AB0` (2134), `0x3310` and `0x3360` (118, both read whole), `0x5007C0` (716, the order's
destructor), `0x870070` (1106) and the four container releases `0x92B340`, `0x92B940`, `0x92BBA0`, `0x92ECB0` (2680). The four
releases are one shape -- recurse into the chain at [node+0x18], free the string, free the node, walk the list at [node+0x10]
-- which is the shape already implemented at 0x9308C0, so they are next, and `0x92ECB0` first because 180 functions call it.

The C++ added so far, for the record, because `forwardedCount` has not moved and the reason should be visible: the launch
order layout (189 lines), the node copy and release (167), the candidate constructor and the module switch (141), and 195
lines of tests that hold them to their RE addresses. None of those is an export entry, so the count stays at 31 until 0x2AB0
itself is written -- which needs the containers, which need the four releases.
"""


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "Where the reader is, and what is implemented" in text:
        print("already there")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text.rstrip("\n") + "\n" + ADD)
    print("appended the status section")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
