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


## Correction (round 534): the launch order is 0x2C0 bytes, and NewLaunchingOrder says so

Round 533 showed the offsets `+0x1C8`, `+0x208`, `+0x240` and `+0x2A8` belong to one object by the overlap of their user
sets, and then overreached: it reported that the object extends past `+0x800` because the offsets keep coming on the same
eight byte grid. A grid is not an object. The extent tool cannot tell one type's members from another type's on the same
numbers, and this is the case that shows it.

The constructor settles it:

    NewLaunchingOrder (0x14620)
        lea rcx, [rip + 0x99925E] ; call 0x64AEA0      ; its own name to the logger
        mov ecx, 0x2C0           ; call 0x998500      ; operator new, 0x2C0 bytes
        movsd [rax + 0x00], xmm0  dword [rax + 0x08] = 0   dword [rax + 0x0C] = 0
        movsd [rax + 0x10], xmm0  dword [rax + 0x18] = 0   dword [rax + 0x1C] = 0
        byte  [rax + 0x20] = 0 ... byte [rax + 0x23] = 0
        movsd [rax + 0x28], xmm0  [rax + 0x30] [rax + 0x38]  byte [rax + 0x40] [rax + 0x41]
        dword [rax + 0x44] [rax + 0x48]  movsd [rax + 0x50]  dword [rax + 0x58]  byte [rax + 0x5C]
        movsd [rax + 0x60]  byte [rax + 0x68] = 1  dword [rax + 0x6C] = 1  movsd [rax + 0x70]
        movsd [rax + 0x78], xmm1  dword [rax + 0x80] = 0  ... to +0x2B8

So the launch order is **exactly 0x2C0 bytes** and the constructor writes every field, which makes the layout evidence
rather than inference. The offsets the extent tool found above `0x2C0` belong to other objects that happen to use the same
low numbers -- the confusion a constructor resolves and a frequency count cannot.

Three things this corrects or confirms:

* `0x5007C0`, the destructor in this objective's closure, receives the order, dereferences it, and walks `+0x1D0`, `+0x1F8`,
  `+0x208`, `+0x228`, `+0x230`, `+0x240`, `+0x250`, `+0x258`, `+0x268`, `+0x270`, `+0x280`, `+0x2A8` and `+0x2B8`. Every one
  is inside 0x2C0, so the destructor is consistent with the constructor and the type is confirmed from both ends.
* `0x22A20` is NOT building the launch order. It allocates 0x1C8, its own field map runs +0 to +0x1C0, and it READS its mode
  from `[order + 0x240]`. It builds a candidate object that refers to the order.
* `0x2AB0` receives the order in rcx, dereferences it into rbp, and reads `[rbp + 0x240]` -- the mode -- which is a member of
  the 0x2C0 launch order, not of the candidate.

### The lesson, which cost two rounds

A structure is found in its CONSTRUCTOR, not in the frequency of its offsets. The frequency tools are useful for finding
candidates and for checking that a claimed member set is plausible, but the moment a constructor is available it is the
authority: one function that writes every field in order gives the size, the field boundaries and the widths at once. The
order to work in is therefore to look for the constructor FIRST -- `NewLaunchingOrder` was already in the recovered name list
from the assertion channel before either round began.


## Embedded sub-objects and record arrays, and how each is found (round 539)

A large structure contains smaller ones by value, and both levels say so in the instructions. Two detectors were built; the
method that works is the second.

### A sub-object is a member whose ADDRESS is derived

    lea rbx, [rcx + 0x120]      ; rbx is the ADDRESS of the member at +0x120 -- a sub-object, not a scalar
    mov eax, [rbx + 0x8]        ; its field
    mov [rbx + 0xC], edx

`re/g_embedded_structs.py` follows those derivations and reports what the derived register touches. Candidates, with the
number of functions that agree on the shape:

| parent | functions | the sub-object's fields |
|---|---:|---|
| `+0x40` | 15 | `+0x10 +0x18 +0x20 +0x28 +0x30 +0x38`, all 8 bytes |
| `+0x38` | 11 | `+0x10 .. +0x30`, all 8 bytes |
| `+0x68` | 6 | eleven 8-byte fields, `+0x10` to `+0x60` |
| `+0x78` | 5 | thirteen 8-byte fields, `+0x10` to `+0x70` |
| `+0x30` | 8 | `+0x10 .. +0x28` |

A shape that twenty functions agree on is a type; one that differs every time is a local. These are the first two levels of
the module's composition, and each can be declared on its own.

### An array of records is found through the COMPUTED element size

The element size is not written anywhere, it is computed where an element address is needed:

    lea rdi, [rax + rax*4]      ; rax * 5
    shl rdi, 3                  ; * 8 = rax * 40 = 0x50

and the container's end pointer uses the same arithmetic:

    lea rax, [rcx + 0x28]       ; the inline buffer
    sub rdx, rax
    shr rdx, 3                  ; the element count
    lea r14, [rsi + rdx*8 + 0x50]   ; begin + count * 8 + 0x50

So `lea reg, [a + b*4] ; shl reg, 3` is the marker for "elements of 0x50 bytes", and 57 functions contain it.
`re/g_element_50.py` reports them and aggregates the fields reached through the element register: `+0x10`, `+0x18` and
`+0x20`, all 8 bytes, which is the same triple the launch order's constructor writes at those offsets -- so the element begins
with the same container header shape.

Two earlier attempts are recorded because each looked reasonable and was wrong: matching any scaled memory reference grouped
the stack with the arrays (44 functions at stride 8 were mostly `[rsp+N]`), and looking for the stride in a displacement
(`lea rdx, [rcx + rax*1 + 0x50]`) found 57 functions and no fields, because this compiler does not write it that way.

**The method is the deliverable**: a type whose size is written nowhere becomes visible the moment the size is computed, and
the computation is a two-instruction shape. The same shape finds 0x10 (`lea r,X*2 ; shl`), 0x30 (`X*3 ; shl 3`), 0x48
(`X*9 ; shl 3`) and any other element size.
