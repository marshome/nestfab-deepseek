# -*- coding: utf-8 -*-
"""Rewrite Tiling::MultitorchEvaluator for the object its constructor builds, which is the cleanest case in the queue.

RE 0x4E8410, 81 BYTES, AND IT IS ALMOST A DECLARATION IN ASSEMBLY:

    0x4E841B  mov rbx, rcx                  ; the MultitorchEvaluator object
    0x4E8419  mov ecx, 0x20 / call 0x998500  ; AN OBJECT OF 0x20 BYTES -- the ONE allocation, and 0x20 is its size
    0x4E8437  lea rdx, [rip + 0x554ee2]      ; ITS vtable, which is NOT this class's (0xA3D320 is) -- so the 0x20 byte object is another type
    0x4E8444  mov [rax], rdx                 ;   installed at its +0
    0x4E8447  mov dword [rax + 8], esi       ; ITS int member, the constructor's SECOND argument
    0x4E844A  movsd [rax + 0x10], xmm2       ; ITS double, the THIRD
    0x4E844F  movsd [rax + 0x18], xmm3       ; ITS double, the FOURTH
    0x4E8454  mov [rbx], rax                 ; AND THE 0x20 BYTE OBJECT IS STORED AT MultitorchEvaluator + 0

**SO THE CLASS IS `{impl* @0}` AND ITS CONSTRUCTOR TAKES (this, int, double, double).** The declaration carried a single `int nbTorches_` and a
one-argument constructor, which passes one of the four values and drops three -- **and the three are the ones the instructions write into the
object.**

AND THE TWO SMALL SLOTS ARE THE SHAPE A LEAF CLASS HAS:
    0x76F250 (slot 1)  jmp 0x9984B0     ; the deleting destructor is a call to the allocator's free
    0x76F260 (slot 0)  ret             ; and slot 0 is an empty function
"""
import io
import sys

TILING = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"

NEW = '''/** RE 0xA3D310, four slots. **ITS OWN STATE IS ONE POINTER AT +0**, and the object it points at is 0x20 bytes with three members.
 *
 *  RE 0x4E8410, 81 bytes, which is nearly a declaration in assembly:
 *
 *      0x4E841B  mov rbx, rcx                     ; this
 *      0x4E8419  mov ecx, 0x20 / call 0x998500     ; AN OBJECT OF 0x20 BYTES
 *      0x4E8437  lea rdx, [rip + 0x554ee2]         ; its own vtable, which is NOT 0xA3D320
 *      0x4E8447  mov dword [rax + 8], esi          ; ITS int   -- the constructor's second argument
 *      0x4E844A  movsd [rax + 0x10], xmm2          ; ITS double -- the third
 *      0x4E844F  movsd [rax + 0x18], xmm3          ; ITS double -- the fourth
 *      0x4E8454  mov [rbx], rax                    ; stored at MultitorchEvaluator + 0
 *
 *  so the constructor takes (this, int, double, double) and this class is a single pointer. The two small slots confirm the shape of a leaf:
 *  slot 1 is `jmp 0x9984B0`, the allocator's free, and slot 0 is a bare `ret`.
 */
class MultitorchEvaluator : public Evaluator {
public:
    /** RE 0x4E8410. **THE DECLARATION HAD ONE PARAMETER AND THE ROUTINE TAKES THREE** -- an int and two doubles, all written into the object
     *  this class allocates. */
    MultitorchEvaluator(int torches, double first, double second);

    const char* name() const override { return "MultitorchEvaluator"; }
    double evaluate(const std::vector<PatternCell>& cells, double sheetArea) const override;

    int torches() const { return impl_.torches; }        // RE 0x4E8447: [impl + 8]
    double first() const { return impl_.first; }         // RE 0x4E844A: [impl + 0x10]
    double second() const { return impl_.second; }       // RE 0x4E844F: [impl + 0x18]

private:
    /** The 0x20 byte object RE 0x4E8419 allocates, with its own vtable at +0. */
    struct Impl {
        void** vtable = nullptr;       // +0x00, RE 0x4E8444
        int torches = 0;               // +0x08, RE 0x4E8447 -- the second argument
        double first = 0.0;            // +0x10, RE 0x4E844A -- the third
        double second = 0.0;           // +0x18, RE 0x4E844F -- the fourth
    };

    Impl impl_{};                      // **BY VALUE**, because RE 0x4E8454 stores the ALLOCATED pointer at +0, so this object IS that memory
};
'''


def main():
    text = io.open(TILING, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find("class MultitorchEvaluator")
    if start < 0:
        print("REFUSING: the class is not found")
        return 2
    end = text.find("\n};\n", start)
    if end < 0:
        print("REFUSING: the closing brace is not found")
        return 2
    # keep the trailing comment on the class line if there is one
    text = text[:start] + NEW + text[end + len("\n};\n"):]
    io.open(TILING, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote Tiling::MultitorchEvaluator's declaration")
    return 0


if __name__ == "__main__":
    sys.exit(main())
