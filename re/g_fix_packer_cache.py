# -*- coding: utf-8 -*-
"""Rewrite Tiling::PackerCache's declaration for the object its constructor builds.

THE CONSTRUCTOR 0x159480, 98 BYTES, AND IT IS AS CLEAR AS Squeezer's:

    0x15948F  mov [rcx], rax              ; the vtable at +0
    0x159492  mov rsi, rcx                ; the PackerCache object
    0x159495  mov ecx, 0x1E0              ; AN INNER OBJECT of 0x1E0 bytes
    0x1594A5  call 0x998500               ; allocated
    0x1594B6  mov rcx, rax / 0x1594BC call 0x76A130   ; CONSTRUCTED, with (this, rdx, r8d, r9b)
    0x1594C1  mov [rsi + 8], rbx          ; AND STORED AT PackerCache + 8

**SO IT IS `{vptr @0, impl* @8}`, THE SAME SHAPE AS Squeezer** -- and the declaration carried a `std::vector<std::string> keys_` and a
`std::size_t entries_` as the class's own state, which no instruction places. The constructor's third and fourth arguments are an `int` and a
`bool` (stored to the stack as r8d and r9d and reloaded as r8d and a zero-extended r9b), so the inner object is constructed from a key and two
flags.
"""
import io
import sys

TILING = r"D:\Nesting\nestfab\lcns\include\lcns\tiling.hpp"

NEW = '''/** RE 0xA3D0E0, two slots. **ITS OWN STATE IS ONE POINTER AT +8.** RE 0x159480, 98 bytes:
 *
 *      0x15948F  mov [rcx], rax                    ; the vtable at +0
 *      0x159495  mov ecx, 0x1E0 / call 0x998500     ; AN INNER OBJECT of 0x1E0 bytes
 *      0x1594BC  call 0x76A130                      ; constructed from (this, rdx, r8d, r9b)
 *      0x1594C1  mov [rsi + 8], rbx                 ; AND STORED AT PackerCache + 8
 *
 *  so this class is `{vptr @0, impl* @8}`, and the inner object at 0x76A130 is what actually caches. The two arguments the constructor
 *  forwards are an **int** and a **bool**: they are saved as `r8d` and `r9d` and reloaded as `r8d` and a zero-extended `r9b`.
 */
class PackerCache {
public:
    void clear();
    std::size_t size() const { return entries_; }
    void store(const std::string& key);
    bool contains(const std::string& key) const;

    /** RE 0x1594C1: the object at +8 that this handle owns and forwards to. */
    void* impl() const { return impl_; }

private:
    // RE 0x15948F: the vtable is at +0, so this is a polymorphic handle.
    void* impl_ = nullptr;             // +8, RE 0x1594C1: mov [rsi + 8], rbx

    // **THE MODEL'S OWN STORAGE, NOT THE MODULE'S.** The module caches inside the 0x1E0 byte object; this keeps a vector and says so, because
    // 0x76A130 -- the routine that fills that object -- has not been read.
    std::vector<std::string> keys_;
    std::size_t entries_ = 0;
};
'''


def main():
    text = io.open(TILING, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    start = text.find("class PackerCache {")
    if start < 0:
        print("REFUSING: the class is not found")
        return 2
    end = text.find("\n};\n", start)
    if end < 0:
        print("REFUSING: the closing brace is not found")
        return 2
    text = text[:start] + NEW + text[end + len("\n};\n"):]
    io.open(TILING, "w", encoding="utf-8", newline="\n").write(text)
    print("rewrote Tiling::PackerCache's declaration")
    return 0


if __name__ == "__main__":
    sys.exit(main())
