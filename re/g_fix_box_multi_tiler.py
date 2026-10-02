# -*- coding: utf-8 -*-
"""Rewrite Tiling::BoxMultiTiler: it is ONE POINTER, and the evaluator vector lives in the object it allocates.

RE 0x4F4850, 883 bytes, and the structure is visible in five instructions:

    0x4F4864  mov r12, rcx               ; this
    0x4F486A  mov qword [rcx], 0         ; ITS ONLY MEMBER, cleared -- and NOT a vtable
    0x4F4B10  mov ecx, 0x188 / call      ; THE INNER OBJECT, 0x188 bytes
    0x4F4887  lea rax, [rip + 0x548882]  ; the INNER object's vtable, installed at its +0 by 0x4F4896
    0x4F4AE0  mov rcx, [r12] / 0x4F4AE4 mov [r12], rsi      ; the inner object replaces the old one
    0x4F4AED  mov rax, [rcx] / 0x4F4AF0 call [rax + 8]      ; THE OLD ONE IS RELEASED THROUGH ITS OWN VTABLE

**THAT LAST PAIR IS THE PROOF THAT THE OBJECT AT +0 IS POLYMORPHIC AND THIS CLASS IS NOT**: a vtable would have been installed at `[r12]` if this
class had one, and instead the only virtual call in the routine goes through the pointer AT +0.

**AND `[rcx]` IS CHECKED AGAINST 0xD18C2E2800** -- the same constant `MultiOrientedPartPattern` stores at its +0x88 -- so that constant is a TYPE TAG
the module compares. `cmp qword [rbx], rax` at 0x4F48A7, with the second argument, and `je` taking the branch that builds from it.

The `r9b` test at 0x4F4861 chooses between the 0x20 byte object at 0x4F487F and the 0x188 byte one at 0x4F4B15, so the constructor has a bool
argument too.
"""
import io
import sys

TILING = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"

NEW = '''/** **ITS OWN STATE IS ONE POINTER AT +0, AND IT IS NOT POLYMORPHIC.**
 *
 *  RE 0x4F4850, 883 bytes:
 *
 *      0x4F4864  mov r12, rcx                  ; this
 *      0x4F486A  mov qword [rcx], 0            ; ITS ONLY MEMBER, cleared -- a POINTER, not a vtable
 *      0x4F4B10  mov ecx, 0x188 / call 0x998500 ; THE INNER OBJECT, 0x188 bytes
 *      0x4F4887  lea rax, [rip + 0x548882]      ; the INNER object's vtable, installed at its +0
 *      0x4F4AE4  mov [r12], rsi                 ; the inner object replaces the old one
 *      0x4F4AED  mov rax, [rcx] / call [rax + 8] ; AND THE OLD ONE IS RELEASED THROUGH ITS OWN VTABLE
 *
 *  **THAT LAST PAIR IS THE PROOF**: a vtable would have been installed at `[r12]` if this class had one, and the only virtual call in the
 *  routine goes through the pointer at +0 instead. So the polymorphic object is the one this class allocates.
 *
 *  AND `[rbx]` -- the second argument -- IS COMPARED AGAINST `0xD18C2E2800` at 0x4F48A7, the same constant `MultiOrientedPartPattern` stores at
 *  its +0x88. **It is a TYPE TAG**, and the comparison is how the constructor recognises what it was handed. The `r9b` test at 0x4F4861 chooses
 *  between a 0x20 byte object and the 0x188 byte one.
 */
class BoxMultiTiler {
public:
    /** RE 0x4F4850. Its second argument is a pointer whose first qword is compared against the type tag, and it has a trailing bool. */
    BoxMultiTiler(const void* tagged, bool flag);

    void add(const std::shared_ptr<Evaluator>& e) { evaluators_.push_back(e); }

    /** returns the best scoring pattern among the candidates */
    std::vector<PatternCell> best(const std::vector<std::vector<PatternCell>>& candidates,
                                 double sheetArea, double* score) const;

    /** RE 0x4F4AE4: the object at +0, whose vtable is the one the constructor installs. */
    void* inner() const { return inner_; }

private:
    /** The 0x188 byte object RE 0x4F4B10 allocates, whose own vtable is installed at its +0. **The evaluator vector lives in IT**, at +8, +0x10
     *  and +0x18 -- the three words a vector needs -- and each element is 0x78 bytes (0x4F4AA5 and 0x4F4AD6 both do `add rbx, 0x78`). */
    struct Inner {
        void** vtable = nullptr;      // +0x00, RE 0x4F4887 and 0x4F4896
        void* begin = nullptr;        // +0x08
        void* end = nullptr;          // +0x10, RE 0x4F4AB0: mov [rsi + 0x10], rax
        void* capacity = nullptr;     // +0x18
    };

    Inner* inner_ = nullptr;          // +0x00, RE 0x4F486A clears it and 0x4F4AE4 replaces it
};
'''


def main():
    text = io.open(TILING, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find("class BoxMultiTiler {")
    if start < 0:
        print("REFUSING: the class is not found")
        return 2
    end = text.find("\n};\n", start)
    if end < 0:
        print("REFUSING: the closing brace is not found")
        return 2
    text = text[:start] + NEW + text[end + len("\n};\n"):]
    io.open(TILING, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote Tiling::BoxMultiTiler's declaration")
    return 0


if __name__ == "__main__":
    sys.exit(main())
