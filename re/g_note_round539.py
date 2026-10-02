# -*- coding: utf-8 -*-
"""Write down the sub-object and array findings: how a nested type and a record type are found in instructions.

Round 539, second half. Three detectors were tried; two were noise and one is a method worth keeping.

  * re/g_embedded_structs.py -- a sub-object shows as a register loaded with the ADDRESS of a member and then dereferenced at
    constant offsets: `lea rbx, [rcx+0x120]` then `[rbx+0x8]`. Real, and it produced candidates: parent +0x40 seen in 15
    functions with fields +0x10..+0x38, parent +0x68 in 6 functions with eleven 8-byte fields, parent +0x78 in 5 functions
    with thirteen. Those are sub-objects with their own layouts, and a repeated shape across many functions is a type rather
    than a local.

  * re/g_arrays.py -- matching any scaled memory reference was noise: `mov [rcx], eax` addresses like a scaled access, so
    the stride-8 group with 44 functions was mostly the stack. Kept only as the record of why the next tool looks for
    something narrower.

  * re/g_stride_records.py -- looking for the stride in a DISPLACEMENT (`lea rdx, [rcx + rax*1 + 0x50]`) found 57 functions
    and no fields, because that is not how this compiler computes an element address.

  * re/g_element_50.py -- the method that works. The element size is COMPUTED, and the computation is findable:

        lea rdi, [rax + rax*4]      ; rax * 5
        shl rdi, 3                  ; * 8 = rax * 40 = 0x50

    and the container end uses the same arithmetic:

        lea rax, [rcx + 0x28]       ; the inline buffer
        sub rdx, rax
        shr rdx, 3                  ; the element count
        lea r14, [rsi + rdx*8 + 0x50]

    so `lea reg,[a + b*4] ; shl reg,3` marks "elements of 0x50 bytes", and 57 functions contain it. The element's fields
    aggregate to +0x10, +0x18, +0x20 (all 8 bytes) among the functions that touch a field through the element register --
    which matches the constructor's +0x10/+0x18/+0x20 members for the same object, so the element begins with a
    container-like triple. The offsets past 0x50 in the aggregate are contamination: several element registers in one body,
    and the tool cannot yet tell which register belongs to which stride.

The method is the deliverable, because a type whose size is written nowhere becomes visible when the size is computed. The
same shape detects any element size: `lea r,X*2 ; shl` is 16 bytes, `X*4 ; shl 3` is 0x50, `X*3 ; shl 3` is 0x30.
"""
import io
import os

PATH = r"D:\Nesting\nestfab\re\findings_structures_shared.md"

NOTE = """

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
"""


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "Embedded sub-objects and record arrays" in text:
        print("already there")
        return 0
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text.rstrip("\n") + "\n" + NOTE)
    print("appended %d characters" % len(NOTE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
