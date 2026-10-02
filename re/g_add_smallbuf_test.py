# -*- coding: utf-8 -*-
"""Test the small-buffer types, which is what layout.hpp's six constants were about."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
ANCHOR = '    return check::finish("test_recovered");'

BLOCK = '''
    // ---------------------------------------------------------------- the small-buffer types (RE 0x6DE480)
    //
    // layout.hpp described this object as six constants and a count with instructions in comments. **That is not C++; it is notes about
    // C++.** These are the types, and the test builds one, which the constants could not do.
    {
        using lcns::BufferView;
        using lcns::SmallBuffer;
        using lcns::BufferOwner;

        CHECK(sizeof(BufferView) == 0x10u);
        CHECK(offsetof(BufferView, data) == 0x00u);
        CHECK(offsetof(BufferView, size) == 0x08u);

        // every member at the offset its instruction places it at
        CHECK(offsetof(SmallBuffer, first) == 0x00u);       // RE 0x6DE49F: mov [rbx], rax
        CHECK(offsetof(SmallBuffer, inline_a) == 0x10u);    // RE 0x6DE493: lea rax, [rax + 0x10]
        CHECK(offsetof(SmallBuffer, second) == 0x20u);      // RE 0x6DE4AC: mov [rbx + 0x20], rax
        CHECK(offsetof(SmallBuffer, inline_b) == 0x30u);    // RE 0x6DE4A8: lea rax, [rbx + 0x30]
        CHECK(offsetof(SmallBuffer, third) == 0x40u);       // RE 0x6DE4C0: mov [rbx + 0x40], rax
        CHECK(offsetof(SmallBuffer, tail) == 0x50u);        // RE 0x6DE4CC: mov byte ptr [rbx + 0x50], 0

        // **AND THE FACT THAT SIX CONSTANTS COULD NOT STATE**: the third pair shares the second's storage, because the constructor computes
        // the address once at 0x6DE4A8 and stores it twice -- at 0x6DE4AC and 0x6DE4C0.
        CHECK(lcns::thirdSharesSecondStorage());

        // an instance can be built and its buffer pairs wired, which is what a type buys
        SmallBuffer buffer;
        buffer.first.data = &buffer.inline_a;
        buffer.first.size = 0;
        buffer.second.data = &buffer.inline_b;
        buffer.second.size = 0;
        buffer.third = buffer.second;                       // RE 0x6DE4C0: the same address
        CHECK(buffer.first.data == &buffer.inline_a);
        CHECK(buffer.second.data == buffer.third.data);
        CHECK(buffer.first.size == 0u && buffer.second.size == 0u);

        // the storage is INSIDE the object, which the pointer arithmetic shows rather than asserts
        const std::byte* base = reinterpret_cast<const std::byte*>(&buffer);
        CHECK(reinterpret_cast<const std::byte*>(&buffer.inline_a) - base == 0x10);
        CHECK(reinterpret_cast<const std::byte*>(&buffer.inline_b) - base == 0x30);
        CHECK(SmallBuffer::kFirstBufferOffset == 0x10u);
        CHECK(SmallBuffer::kSecondBufferOffset == 0x30u);
        CHECK(SmallBuffer::kSubBlockBytes == 0x18u);

        // the owner block, whose vtable makes it polymorphic and whose refcounts start at one
        BufferOwner owner{};
        CHECK(offsetof(BufferOwner, vtable) == 0x00u);      // RE 0x6DE4F5
        CHECK(offsetof(BufferOwner, refcount) == 0x08u);    // RE 0x6DE4E7
        CHECK(offsetof(BufferOwner, flags) == 0x0Cu);       // RE 0x6DE4EE
        CHECK(offsetof(BufferOwner, payload) == 0x10u);     // RE 0x6DE4D9
        CHECK(BufferOwner::kVtableRva == 0x35E739u);        // RE 0x6DE4E0
        CHECK(BufferOwner::kBytes == 0x60u);                // RE 0x6DE4D0
        CHECK(owner.refcount == 1u && owner.flags == 1u);
        owner.payload = &buffer;
        CHECK(owner.payload == &buffer);
    }
'''


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "thirdSharesSecondStorage" in text:
        print("already present")
        return 0
    include = '#include "lcns/small_buffer.hpp"\n'
    if include not in text:
        anchor = '#include "lcns/records.hpp"\n'
        assert anchor in text, "the records include is gone"
        text = text.replace(anchor, anchor + include, 1)
        print("include added")
    text = text.replace(ANCHOR, BLOCK + "\n" + ANCHOR, 1)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("small-buffer test added; lines now %d" % text.count("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
