# -*- coding: utf-8 -*-
"""Rewrite Tiling::MultiOrientedPartPattern for the object its constructor builds, whose fields are INLINE.

RE 0x4F2910, 285 bytes. **THE CLASS IS THE 0x90 BYTE BLOCK IT ALLOCATES** -- because the vtable installed at 0x4F2940 is its OWN:

    0x4F2917  mov rdi, rcx              ; the destination, a 2 machine word handle the CALLER owns
    0x4F291A  mov ecx, 0x90 / call      ; THE CLASS: 0x90 bytes
    0x4F292C  mov rbx, rax
    0x4F292F  lea rax, [rip + 0x54aa4a] ; = 0xA3D380, and 0xA3D370 is `Tiling::MultiOrientedPartPattern`
    0x4F2940  mov [rbx], rax            ; so rbx IS this class
    0x4F2936  mov dword [rbx + 0x80], 4 ; a count of 4
    0x4F2943..4F29B6  copies 0x70 bytes from rsi into [rbx + 8] through [rbx + 0x78]
    0x4F29C4  mov qword [rbx + 0x88], 0xD18C2E2800   ; = 900000000000
    0x4F29CB  mov [rdi], rbx            ; the caller's handle takes the object
    0x4F29D6  mov ecx, 0x18 / call      ; A CONTROL BLOCK of 0x18 bytes
    0x4F29F0  mov [rax], rdx            ; its own vtable at 0xA56140
    0x4F29E2  mov dword [rax + 8], 1 / 0x4F29E9 [rax + 0xc], 1    ; TWO reference counts, both 1
    0x4F29F3  mov [rax + 0x10], rbx     ; pointing back at the object
    0x4F29F7  mov [rdi + 8], rax        ; and the SECOND word of the caller's handle

**SO THE CLASS'S FIELDS ARE INLINE**, and the `{object, control}` pair is a REFERENCE-COUNTED HANDLE THAT BELONGS TO THE CALLER -- in the profile's
call site it is a stack temporary. **Three of the class's own slots confirm the offsets:**

    slot 2  0x7EBB90  reads [this + 0x88]     ; the 900000000000 constant
    slot 3  0x7EB5E0  reads [this + 0x10]     ; inside the copied region
    slot 4  0x7EBC30  reads [this + 0x80]     ; the count of 4

**WHICH IS WHY THE DECLARATION'S FIVE FIELDS WERE NOT UNSUPPORTED BUT UNPLACED**: `partIndex_`, `cellW_`, `cellH_` and `spacing_` are this
project's own layout for a class whose real state is a 0x70 byte configuration copied in, a count and a constant.
"""
import io
import sys

TILING = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"

NEW = '''/** RE 0xA3D370, five slots. **THE CLASS IS A 0x90 BYTE OBJECT AND ITS FIELDS ARE INLINE.**
 *
 *  RE 0x4F2910, 285 bytes:
 *
 *      0x4F2917  mov rdi, rcx                      ; the destination -- a 2 word handle the CALLER owns
 *      0x4F291A  mov ecx, 0x90 / call 0x998500      ; THE CLASS, 0x90 bytes
 *      0x4F292F  lea rax, [rip + 0x54aa4a]          ; = 0xA3D380, and 0xA3D370 is THIS class
 *      0x4F2940  mov [rbx], rax                     ; so rbx IS this object
 *      0x4F2936  mov dword [rbx + 0x80], 4          ; a count of 4
 *      0x4F2943  copies 0x70 bytes from rsi into [rbx + 8] .. [rbx + 0x78]
 *      0x4F29C4  mov qword [rbx + 0x88], 0xD18C2E2800   ; = 900000000000
 *      0x4F29CB  mov [rdi], rbx                     ; the caller's handle takes the object
 *      0x4F29D6  mov ecx, 0x18 / call 0x998500       ; A CONTROL BLOCK of 0x18 bytes
 *      0x4F29F0  mov [rax], rdx                     ; its vtable at 0xA56140
 *      0x4F29E2  mov dword [rax + 8], 1             ; TWO reference counts, both 1
 *      0x4F29E9  mov dword [rax + 0xc], 1
 *      0x4F29F3  mov [rax + 0x10], rbx              ; pointing back at the object
 *      0x4F29F7  mov [rdi + 8], rax                 ; the second word of the caller's handle
 *
 *  **SO THE `{object, control}` PAIR IS A REFERENCE-COUNTED HANDLE THAT BELONGS TO THE CALLER**, and the class itself is the 0x90 bytes. Three
 *  of the class's own slots place its offsets: slot 2 at 0x7EBB90 reads +0x88, slot 3 at 0x7EB5E0 reads +0x10, and slot 4 at 0x7EBC30 reads
 *  +0x80.
 */
class MultiOrientedPartPattern {
public:
    /** RE 0x4F2910. **THE ROUTINE TAKES A CONFIGURATION POINTER AND COPIES 0x70 BYTES OF IT**, so the constructor's argument is not an index. */
    explicit MultiOrientedPartPattern(const PatternConfig& config);

    void addOrientation(double angleRadians, bool flipped);   // the model's own; NOT a slot of the module's class
    void setCellSize(double w, double h);                     // and this one likewise
    void setSpacing(double spacing) { spacing_ = spacing; }

    std::vector<PatternCell> layout(double sheetW, double sheetH, int budget) const;
    std::size_t orientationCount() const { return orientations_.size(); }

    /** The state the module keeps INLINE, which is what its own slots read. */
    std::uint32_t capacity() const { return capacity_; }        // +0x80, RE 0x4F2936 and slot 4
    std::uint64_t limit() const { return limit_; }              // +0x88, RE 0x4F29C4 and slot 2

    /** The 0x70 bytes RE 0x4F2943 copies in, at +8 through +0x78. **Its fields are not established field by field**, so it is carried as the
     *  byte block the instruction copies rather than given names that would be guesses. */
    struct Inline {
        std::byte bytes[0x70]{};
    };

    /** What the constructor copies FROM. The same 0x70 bytes, read at rsi. */
    struct PatternConfig {
        std::byte bytes[0x70]{};
    };

private:
    Inline inline_{};                      // +0x08 .. +0x78, RE 0x4F2943
    std::uint32_t capacity_ = 0;           // +0x80, RE 0x4F2936: mov dword [rbx + 0x80], 4
    std::uint32_t padding_ = 0;            // +0x84, so that +0x88 is 8 byte aligned
    std::uint64_t limit_ = 0;              // +0x88, RE 0x4F29C4: movabs rax, 0xD18C2E2800

    // **THE MODEL'S OWN STORAGE, NOT THE MODULE'S.** The module's orientation data is inside the 0x70 bytes at +8; this keeps a vector so the
    // port can place the same calls, because those bytes have not been read field by field.
    struct Orientation {
        double angle;
        bool flipped;
    };
    int partIndex_ = 0;
    std::vector<Orientation> orientations_;
    double cellW_ = 0.0;
    double cellH_ = 0.0;
    double spacing_ = 0.0;
};
'''


def main():
    text = io.open(TILING, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find("class MultiOrientedPartPattern {")
    if start < 0:
        print("REFUSING: the class is not found")
        return 2
    end = text.find("\n};\n", start)
    if end < 0:
        print("REFUSING: the closing brace is not found")
        return 2
    text = text[:start] + NEW + text[end + len("\n};\n"):]
    io.open(TILING, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote Tiling::MultiOrientedPartPattern's declaration")
    return 0


if __name__ == "__main__":
    sys.exit(main())
