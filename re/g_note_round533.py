# -*- coding: utf-8 -*-
"""Write the shared-structure finding: how the offsets of one object were shown to belong together.

Round 533. The question was where this module's reuse hides, and the answer is in the offsets rather than in the call graph.
re/g_same_type.py compares the user sets of two offsets; re/g_members.py prints one function's offsets grouped by the
register that carries the object, marking the register that holds the first argument.

What the two found:

  +0x240   64 functions   FillNestingAux, Implementation, InsertAllNext, InsertMonoMultiplicity, NewLaunchingOrder,
                           SetCommonCutParameters
  +0x2A8   97 functions   AddOrReplaceEquiv, ComputeSheetGeometryRowMode, DeleteLaunchingOrder, FillNestingAux,
                           Implementation, InsertAllNext
  +0x1C8  147 functions   AddOrReplaceEquiv, DeleteLaunchingOrder, FillNestingAux, Implementation,
                           InsertMonoMultiplicity, NewLaunchingOrder
  +0x208  118 functions   ComputeSheetGeometryRowMode, FillNestingAux, Implementation, InsertMonoMultiplicity, Postop,
                           SetCommonCutParameters

    0x240 and 0x2A8: 37 functions in common (58% of 0x240)
    0x240 and 0x1C8: 40 in common (62% of 0x240)
    0x2A8 and 0x208: 46 in common (47% of 0x2A8)

So the offsets are the same object, and the object is the LaunchingOrder: NewLaunchingOrder, DeleteLaunchingOrder,
SetCommonCutParameters, SetMultiTorchParameters, FillNestingAux and Implementation all appear in the intersections. This
was not assumed -- it is the overlap of the user sets, and the file records both fractions for every pair so a small
accidental overlap cannot be mistaken for a type.

Two consequences for the objective:

* 0x2AB0's mode at [order + 0x240] is a member of the launch order, which is why the constructor reads it: a mode of the
  order, not of the candidate.
* The object 0x22A20 builds is 0x1C8 bytes, and the offsets above it -- +0x1D0 through +0x800, still on the same eight byte
  grid, still touched by thirty to a hundred and seventy functions -- belong to that same type in the destructor 0x5007C0
  and in 0x870070. 0x1C8 is the part the constructor initialises; it is not the end of the object.

Also recorded, because it is the one structure in this objective whose layout is fully certain: the 0x48 byte node that
0x9302C0 copies and 0x9308C0 frees. re/g_members.py 0x92B340 prints it directly -- five registers, each with exactly
+0x10:8 +0x18:8 +0x20:8 +0x30:8 -- so the node is a back pointer at +0x10, a forward pointer at +0x18, an inline string at
+0x20 whose buffer is the node's own +0x30, and a type dword at +0, with the double at +0x40 that 0x9302C0 also copies.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"


def main():
    note = '''

## The shared structures, and how they were shown to be one (round 533)

The question "which structures do many functions use" is a question about offsets, and the tool that answers it compares
offset USER SETS rather than counting users. `re/g_same_type.py` prints, for two offsets, how many functions touch both and
what fraction that is of each -- and `re/g_members.py` prints one function's offsets grouped by the register that carries the
object, marking the register that holds the first argument, which is how a member list is read out of a function.

### The launch order

| offset | functions | some of the named users |
|---|---:|---|
| `+0x1C8` | 147 | `AddOrReplaceEquiv`, `DeleteLaunchingOrder`, `FillNestingAux`, `Implementation`, `NewLaunchingOrder` |
| `+0x208` | 118 | `ComputeSheetGeometryRowMode`, `FillNestingAux`, `Implementation`, `Postop`, `SetCommonCutParameters` |
| `+0x240` | 64 | `FillNestingAux`, `Implementation`, `InsertAllNext`, `InsertMonoMultiplicity`, `NewLaunchingOrder` |
| `+0x2A8` | 97 | `AddOrReplaceEquiv`, `ComputeSheetGeometryRowMode`, `DeleteLaunchingOrder`, `Implementation` |

Overlaps: `+0x240` and `+0x1C8` share 40 functions (62% of `+0x240`'s users); `+0x240` and `+0x2A8` share 37 (58%);
`+0x2A8` and `+0x208` share 46 (47%). That is the same object, and the object is the LaunchingOrder -- `NewLaunchingOrder`,
`DeleteLaunchingOrder`, `SetCommonCutParameters`, `SetMultiTorchParameters`, `FillNestingAux` and `Implementation` appear in
the intersections. Both fractions are recorded for every pair so that a small accidental overlap cannot pass for a type.

Two things follow for the LaunchLocalComputation objective:

* the mode that `0x22A20` reads at `[order + 0x240]` is a member of the launch order, so the iteration cap and the two
  doubles it configures are the ORDER's mode, not the candidate's;
* the offsets above `+0x1C8` -- `+0x1D0` to `+0x800`, still on the same eight byte grid, still touched by thirty to a hundred
  and seventy functions -- belong to the same type in `0x5007C0` and `0x870070`. The `0x1C8` bytes `0x22A20` allocates are
  the part the constructor initialises, not the end of the object.

### The 0x48 byte node

The one structure here whose layout is completely certain, because five registers in one function show it at once --
`re/g_members.py 0x92B340` prints `r12`, `r13`, `r14`, `r15` and `rdi` each with exactly `+0x10:8 +0x18:8 +0x20:8 +0x30:8`:
a back pointer at `+0x10`, a forward pointer at `+0x18`, an inline string at `+0x20` whose buffer is the node's own `+0x30`,
a type dword at `+0`, and the double at `+0x40` that `0x9302C0` also copies. `0x9308C0` frees the string only when `+0x20` is
not the node's own `+0x30`, which is what the inline buffer rule looks like in code.
'''

    path = os.path.join(ROOT, "re", "findings_structures_shared.md")
    io.open(path, "w", encoding="utf-8", newline="\n").write(note.lstrip("\n"))
    print("wrote %s (%d characters)" % (path, len(note)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
