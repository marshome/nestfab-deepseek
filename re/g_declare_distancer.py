# -*- coding: utf-8 -*-
"""Declare Row::Distancer -- the abstract base lcns/row.hpp never had -- and make Squeezer derive from it.

**THE MODULE'S OWN RTTI SAYS SO, WHICH IS AN ORACLE RATHER THAN A SHAPE.** `Row::Squeezer`'s vtable is at 0xA3B1E0, its typeinfo at 0xA17E00, and the
typeinfo's +0x10 points at 0xA17E60 whose name string is `N3Row9DistancerE`. So:

    Row::Squeezer  ->  Row::Distancer

**AND THE INTERFACE IS READABLE FROM THE SIBLING THAT DOES HAVE A VTABLE.** `Row::BasicDistancer` at 0xA3B1B0 has three slots:

    0x679060  ret                        ; slot 0: the deleting destructor's abstract placeholder
    0x679050  jmp 0x9984B0               ; slot 1: the destructor, tail calling the allocator
    0x7CA810  movsd xmm0, [rcx + 8]      ; slot 2: THE ONE VIRTUAL METHOD -- it returns the double at +8
              ret

**AND THAT IS EXACTLY WHAT Squeezer PUTS AT ITS +8**: RE 0x138B5C is `mov [rbp + 8], rbx`, storing the 0x270 byte Impl there. So `Squeezer` implements
the interface by handing back a double out of the object it allocated, and the abstract base's whole surface is that one accessor.
"""
import io
import sys

ROW = r"D:\Nesting\nestfab\lcns\include\lcns\row.hpp"

BASES = '''/** **THE ABSTRACT BASE lcns/row.hpp NEVER HAD**, named by the module's own RTTI: `Row::Squeezer`'s typeinfo at 0xA17E00 points at 0xA17E60, whose
 *  name string is `N3Row9DistancerE`.
 *
 *  **ITS INTERFACE IS READABLE FROM THE SIBLING THAT HAS A VTABLE.** `Row::BasicDistancer` at 0xA3B1B0 has three slots:
 *
 *      0x679060  ret                       ; slot 0: the deleting destructor's abstract placeholder
 *      0x679050  jmp 0x9984B0              ; slot 1: the destructor, tail calling the allocator
 *      0x7CA810  movsd xmm0, [rcx + 8]     ; slot 2: THE ONE VIRTUAL METHOD -- it returns the double at +8
 *                ret
 *
 *  so the base's whole surface is one accessor, and a class deriving from it is one that can hand back a `double`.
 *
 *  **`Row::Distancer` ITSELF HAS NO INSTANTIATED VTABLE AND IS THEREFORE NOT A KEY IN re/vtables.json**, which is why it went unnoticed while every
 *  class in this header was written as a standalone type. */
class Distancer {
public:
    virtual ~Distancer() = default;

    /** RE 0x7CA810: `movsd xmm0, qword ptr [rcx + 8]` then `ret`. A double, read at +8 of the object. */
    virtual double distance() const = 0;
};

'''

OLD = """    /** RE 0xA3B1F0, three slots. **ITS OWN STATE IS ONE POINTER.** The constructor installs the vtable at +0, allocates the 0x270 byte Impl and
     *  stores it at +8, and touches nothing else of this object -- so `Impl` is where the fields are, and this class is the handle.
     *
     *  The cost path below the constructor reads the SCALARS through that pointer, which is why `enabled`, `threshold`, `coeff` and
     *  `twiceMaxExtent` are accessors here rather than members. */
    class Squeezer {"""

NEW = """    /** **RE 0xA3B1E0, AND IT DERIVES FROM `Distancer`** -- the module's own RTTI says so: the typeinfo at 0xA17E00 names this class and its +0x10
     *  points at 0xA17E60, whose name is `N3Row9DistancerE`.
     *
     *  Its state is ONE POINTER at +8, and that is also where the base's only virtual method looks: 0x7CA810 is `movsd xmm0, [rcx + 8]`. **SO
     *  `distance()` RETURNS A DOUBLE OUT OF THE OBJECT THE CONSTRUCTOR ALLOCATED**, which is the coherent reading of both instructions at once.
     *
     *  RE 0x138A20 installs the vtable, allocates the 0x270 byte Impl and stores it at +8, and touches nothing else of this object. */
    class Squeezer : public Distancer {"""


def main():
    text = io.open(ROW, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "class Distancer" in text:
        print("Distancer is already declared")
        return 0
    anchor = "    /** The 0x270 byte object RE 0x138A20 allocates"
    if anchor not in text:
        print("REFUSING: the Squeezer Impl comment is not found")
        return 2
    text = text.replace(anchor, BASES + anchor, 1)
    if OLD not in text:
        print("REFUSING: Squeezer's class comment is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    # the interface's method must be implemented, since Squeezer's +8 IS the double the base's slot 2 reads
    text = text.replace(
        "        double twiceMaxExtent() const { return impl_ != nullptr ? impl_->twiceMaxExtent : 0.0; }",
        "        double twiceMaxExtent() const { return impl_ != nullptr ? impl_->twiceMaxExtent : 0.0; }\n\n"
        "        /** RE 0x7CA810: the base's only virtual method reads the double at +8, and `impl_` IS what this class stores there\n"
        "         *  (`mov [rbp + 8], rbx` at 0x138B5C). So the implementation hands back the extent. */\n"
        "        double distance() const override { return twiceMaxExtent(); }", 1)
    io.open(ROW, "w", encoding="utf-8", newline="\n").write(text)
    print("declared Row::Distancer, made Squeezer derive from it, and implemented distance()")
    return 0


if __name__ == "__main__":
    sys.exit(main())
