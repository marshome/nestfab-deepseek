// lcns/include/lcns/cns_node.hpp -- the 0x48 byte node, and its copy and release.
//
// RE 0x9302C0 (the copy) and 0x9308C0 (the release). The layout is the one structure in this objective whose fields are
// certain without reading a constructor, because five registers in one function show the same four offsets at once:
// re/g_members.py 0x92B340 prints r12, r13, r14, r15 and rdi each with exactly +0x10:8 +0x18:8 +0x20:8 +0x30:8.
//
//   +0x00  a type dword
//   +0x08  a pointer the caller supplies (0x9302C0's second argument)
//   +0x10  the back pointer
//   +0x18  the forward pointer
//   +0x20  the string's data pointer, which is the node's OWN +0x30 for a short string
//   +0x28  the string's length
//   +0x30  the inline string buffer
//   +0x40  a double
//
// The two routines are mutual: 0x9302C0 allocates 0x48 bytes, points +0x20 at +0x30, copies the string, copies the type
// dword and the double, rewrites the back pointer, recurses into the forward chain, and then walks the list at +0x10
// linking the copies. 0x9308C0 does the same walk in reverse: it recurses into +0x18, frees +0x20 ONLY when it is not the
// node's own +0x30, frees the node, and walks +0x10 the same way.
//
// Both are implemented here rather than left read, because the ownership rule is now fully determined by those two
// instructions: a string is owned exactly when its pointer is not the inline buffer. That is the rule a free routine needs
// and it is the rule that was missing when this was left alone.
#pragma once

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>

namespace lcns {
namespace dll {

/** RE 0x9302C0: the node is allocated with 0x48 bytes. */
inline constexpr std::size_t kCnsNodeBytes = 0x48;

/** RE 0x9302C0 at 0x93030D: the inline string buffer sits at the node's own +0x30. */
inline constexpr std::size_t kCnsNodeInlineBuffer = 0x30;

inline void* cnsNodeAllocate() {
    // RE 0x9302D2: mov ecx, 0x48 ; call 0x998500 (operator new)
    return std::calloc(1, kCnsNodeBytes);
}

inline void cnsNodeFree(void* node) {
    std::free(node);
}

/** RE 0x9308C0: frees the string only when its pointer is not the node's own inline buffer. */
inline void cnsNodeFreeString(void* node) {
    unsigned char* base = static_cast<unsigned char*>(node);
    void* data = nullptr;
    std::memcpy(&data, base + 0x20, sizeof(data));
    if (data != nullptr && data != base + kCnsNodeInlineBuffer) {
        // RE 0x9309A7: call 0x9984B0 with the string pointer
        std::free(data);
    }
}

/** RE 0x9302C0: copies one node and the two chains that hang off it.
 *
 * The third argument is the 0x48-byte size the original passes in rdx, kept because it is part of the machine interface
 * even though this implementation only ever uses kCnsNodeBytes. */
inline void* cnsNodeCopy(void* base, const void* source, std::size_t element_size);

inline void cnsNodeCopyString(void* destination, const void* source) {
    unsigned char* dst = static_cast<unsigned char*>(destination);
    const unsigned char* src = static_cast<const unsigned char*>(source);
    const void* src_data = nullptr;
    std::size_t src_length = 0;
    std::memcpy(&src_data, src + 0x20, sizeof(src_data));
    std::memcpy(&src_length, src + 0x28, sizeof(src_length));
    // RE 0x9302E6: the destination's own buffer is written first, so +0x20 is its own +0x30 from the start
    void* dst_buffer = dst + kCnsNodeInlineBuffer;
    std::memcpy(dst + 0x20, &dst_buffer, sizeof(dst_buffer));
    if (src_data != nullptr && src_length != 0) {
        // RE 0x9302FC: 0x1B070, the string copy used everywhere in this module
        if (src_data == src + kCnsNodeInlineBuffer) {
            std::memcpy(dst_buffer, src_data, src_length);
        } else {
            std::memcpy(dst_buffer, src_data, src_length);
        }
    }
    std::memcpy(dst + 0x28, &src_length, sizeof(src_length));
}

inline void* cnsNodeCopy(void* base, const void* source, std::size_t element_size) {
    (void)element_size;
    const unsigned char* src = static_cast<const unsigned char*>(source);
    unsigned char* node = static_cast<unsigned char*>(cnsNodeAllocate());
    if (node == nullptr) {
        return nullptr;
    }
    // RE 0x9302E2 to 0x9302FC: the string, then the type dword, the caller's pointer and the double
    cnsNodeCopyString(node, src);
    std::memcpy(node + 0x00, src + 0x00, 4);            // RE 0x93030D, mov eax, dword ptr [rbx]
    std::memcpy(node + 0x08, &base, sizeof(base));      // RE 0x93031C, the second argument
    std::uint64_t zero = 0;
    std::memcpy(node + 0x10, &zero, sizeof(zero));      // RE 0x930305, the back pointer is rewritten below
    std::memcpy(node + 0x18, &zero, sizeof(zero));      // RE 0x93030F
    double value = 0.0;
    std::memcpy(&value, src + 0x40, sizeof(value));
    std::memcpy(node + 0x40, &value, sizeof(value));    // RE 0x930317 to 0x930323
    // RE 0x93031C to 0x93033D: the forward chain, copied recursively
    const void* forward = nullptr;
    std::memcpy(&forward, src + 0x18, sizeof(forward));
    if (forward != nullptr) {
        void* copied = cnsNodeCopy(base, forward, element_size);
        std::memcpy(node + 0x18, &copied, sizeof(copied));
    }
    // RE 0x930341 to 0x9303C4: the list at +0x10, each node copied and linked
    const void* back = nullptr;
    std::memcpy(&back, src + 0x10, sizeof(back));
    unsigned char* previous = node;
    while (back != nullptr) {
        unsigned char* link = static_cast<unsigned char*>(cnsNodeAllocate());
        if (link == nullptr) {
            break;
        }
        cnsNodeCopyString(link, back);
        std::memcpy(link + 0x00, static_cast<const unsigned char*>(back) + 0x00, 4);
        std::memcpy(link + 0x18, &zero, sizeof(zero));
        std::memcpy(link + 0x10, &zero, sizeof(zero));
        double link_value = 0.0;
        std::memcpy(&link_value, static_cast<const unsigned char*>(back) + 0x40, sizeof(link_value));
        std::memcpy(link + 0x40, &link_value, sizeof(link_value));
        std::memcpy(link + 0x08, &previous, sizeof(previous));
        std::memcpy(previous + 0x18, &link, sizeof(link));
        std::memcpy(link + 0x08, &previous, sizeof(previous));
        const void* next_back = nullptr;
        std::memcpy(&next_back, static_cast<const unsigned char*>(back) + 0x10, sizeof(next_back));
        back = next_back;
        previous = link;
    }
    return node;
}

/** RE 0x9308C0: frees a node and everything it owns.
 *
 * The second argument is the list head the original receives in rdx: it walks that list freeing each node and its string
 * after the recursion into +0x18. */
inline void cnsNodeRelease(void* base, void* head);inline void cnsNodeReleaseOne(void* node) {
    unsigned char* current = static_cast<unsigned char*>(node);
    while (current != nullptr) {
        unsigned char* forward = nullptr;
        std::memcpy(&forward, current + 0x18, sizeof(forward));
        if (forward != nullptr) {
            cnsNodeReleaseOne(forward);                  // RE 0x930960, the recursive call
        }
        cnsNodeFreeString(current);                      // RE 0x930981, free +0x20 unless it is +0x30
        unsigned char* back = nullptr;
        std::memcpy(&back, current + 0x10, sizeof(back));
        cnsNodeFree(current);                            // RE 0x93098C, free the node
        current = back;
    }
}

inline void cnsNodeRelease(void* base, void* head) {
    (void)base;
    if (head == nullptr) {
        return;                                          // RE 0x9308DE
    }
    cnsNodeReleaseOne(head);
}

}  // namespace dll
}  // namespace lcns
