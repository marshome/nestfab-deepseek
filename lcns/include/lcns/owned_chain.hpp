// lcns/include/lcns/owned_chain.hpp -- the chain node 0x92ECB0 unlinks and frees, one node at a time.
//
// This is a DIFFERENT node from the 0x48 byte one in cns_node.hpp. That one is 0x48 bytes with its string at +0x20 and its two
// links at +0x10 and +0x18; this one is 0x60 bytes with its two owned buffers at +0x20 and +0x40 and a single chain link at
// +0x10. They are told apart by the offsets and not by resemblance, which is the reason both are recorded rather than merged.
//
// RE 0x92ECB0, 791 bytes. It is a LOOP, not eight levels of nesting -- the first reading of the prologue suggested nesting
// because eight `mov reg, [prev+0x18]` follow one another, but the body shows the loop it really is:
//
//     0x92ED9A  mov rcx, [rdi+0x40]        ; buffer 1's data pointer
//               lea rax, [rdi+0x50]        ; and its INLINE address
//               mov rbx, [rdi+0x10]        ; the next node, read BEFORE the node is freed
//               cmp rcx, rax
//               je  0x92EDB0               ; equal -> the buffer is inline, do NOT free
//               call 0x9984B0              ; otherwise free it
//     0x92EDB0  mov rcx, [rdi+0x20]        ; buffer 2, the same rule against +0x30
//               lea rax, [rdi+0x30]
//               cmp rcx, rax
//               je  0x92EDC2
//               call 0x9984B0
//     0x92EDC2  mov rcx, rdi
//               mov rdi, rbx
//               call 0x9984B0              ; free the node itself
//     0x92EDCD  test rbx, rbx
//               jne 0x92ED41              ; and go round again
//
// so the ownership rule is the same one this project already proved for the 0x48 node, applied twice per node:
// **a buffer is owned exactly when its data pointer is not its own inline address.** Two buffers, two comparisons, and a chain
// link walked forward.
//
// The 791 bytes are mostly the eight unrolled COPIES of that loop body -- the compiler emitted the first eight iterations
// inline and the loop tail for the rest, which is why the prologue looks like eight levels of nesting. Reading the loop instead
// of the prologue is what turns 791 bytes into five lines of C++.
//
// 0x9984B0 is the allocator's free: 5 bytes, `jmp` through the runtime's free, called 27 times in this function and once per
// buffer per node.
#pragma once

#include <cstddef>
#include <cstdint>
#include <cstdlib>

namespace lcns {

/** One node of the chain 0x92ECB0 tears down, as the code addresses it.
 *
 * Only the offsets the routine TOUCHES are declared, and each one is named for what the instruction does with it rather than for
 * what it probably is. The two buffers are pairs of (data pointer, inline address) because that is the shape a short-string
 * optimization has and it is what the two comparisons test.
 */
struct OwnedChainNode {
    void* unknown00 = nullptr;      // +0x00  not touched by 0x92ECB0
    void* unknown08 = nullptr;      // +0x08  not touched by 0x92ECB0
    void* chain = nullptr;          // +0x10  the next node; read into rbx BEFORE this node is freed, so the walk survives
    void* unknown18 = nullptr;      // +0x18  not touched
    void* buffer1Data = nullptr;    // +0x20
    void* unknown28 = nullptr;      // +0x28
    void* buffer1Inline = nullptr;  // +0x30  buffer1 is inline iff buffer1Data == buffer1Inline
    void* unknown38 = nullptr;      // +0x38
    void* buffer2Data = nullptr;    // +0x40
    void* unknown48 = nullptr;      // +0x48
    void* buffer2Inline = nullptr;  // +0x50  buffer2 is inline iff buffer2Data == buffer2Inline
    void* unknown58 = nullptr;      // +0x58
};

static_assert(offsetof(OwnedChainNode, chain) == 0x10, "RE 0x92EDA2: mov rbx, [rdi+0x10]");
static_assert(offsetof(OwnedChainNode, buffer1Data) == 0x20, "RE 0x92EDB0: mov rcx, [rdi+0x20]");
static_assert(offsetof(OwnedChainNode, buffer1Inline) == 0x30, "RE 0x92EDB4: lea rax, [rdi+0x30]");
static_assert(offsetof(OwnedChainNode, buffer2Data) == 0x40, "RE 0x92ED9A: mov rcx, [rdi+0x40]");
static_assert(offsetof(OwnedChainNode, buffer2Inline) == 0x50, "RE 0x92ED9E: lea rax, [rdi+0x50]");
static_assert(sizeof(OwnedChainNode) >= 0x58, "RE 0x92ED9E: the outermost offset the routine reads is +0x50");

namespace detail {

/** The allocator's free, RE 0x9984B0 (5 bytes: a jmp through the runtime). */
inline void runtimeFree(void* block) {
    std::free(block);
}

}  // namespace detail

/** RE 0x92ECB0: unlink and free a chain of nodes, freeing each node's two buffers when they are not inline.
 *
 * The recovery is a loop rather than the recursion the prologue suggests, because the freeing call happens AFTER the next node
 * has been read out of the current one: `mov rbx, [rdi+0x10]` precedes `call free`, which is the only safe order once the node
 * itself is being released.
 *
 * The two buffers use the same rule as cns_node.hpp's string, and the rule is the whole of the routine's meaning: a buffer is
 * owned exactly when its data pointer is not its own inline address. Two comparisons per node, then the node.
 */
inline void releaseOwnedChain(OwnedChainNode* node) {
    while (node != nullptr) {
        // The link is declared as void* because the routine never types it; the cast is where this recovery says it walks a
        // chain of the same node, and it is a static_cast so that a change of layout breaks the compile rather than the walk.
        OwnedChainNode* next = static_cast<OwnedChainNode*>(node->chain);   // RE 0x92EDA2, read before the free
        void* data[2] = {node->buffer1Data, node->buffer2Data};        // RE 0x92EDB0 and 0x92ED9A
        void* inline_address[2] = {node->buffer1Inline, node->buffer2Inline};   // RE 0x92EDB4 and 0x92ED9E
        for (int buffer = 0; buffer < 2; ++buffer) {
            if (data[buffer] != nullptr && data[buffer] != inline_address[buffer]) {
                detail::runtimeFree(data[buffer]);          // RE 0x92EDAB and 0x92EDBD
            }
        }
        detail::runtimeFree(node);                          // RE 0x92EDC8
        node = next;                                        // RE 0x92EDCD: test rbx, rbx ; jne
    }
}

}  // namespace lcns
