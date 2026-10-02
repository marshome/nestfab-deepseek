// lcns/include/lcns/chain_release.hpp -- the deeper chain release: 0x18 links, 9 frees, 35 identical copies (RE 0x923110).
//
// RE 0x923110, 408 bytes, 113 instructions, and THIRTY-FIVE functions in the module are byte-identical to it apart from their own
// addresses -- re/g_identical_functions.py found the group by normalising code addresses away and keeping constants. So this is one
// routine the compiler emitted thirty-five times, which is what a per-type destructor generated from a template looks like.
//
// Its structure:
//
//     0x923120  test rdx, rdx / je <done>          ; a null argument is a no-op
//     0x92313C  mov rax, [rax + 0x18]              ; THE CHAIN LINK
//               test rax, rax / je <level 6>
//     0x92314E  mov rax, [rax + 0x18]              ; and again, seven times unrolled
//               ...
//     0x92317A  mov r15, [r14 + 0x18]
//               ... 9 calls to 0x9984B0 (the allocator's free)
//     0x923291  jne 0x923134                       ; AND BACK TO THE TOP: it is a loop
//     0x923297  add rsp, 0x38 / eight pops / ret
//
// so it walks a chain whose link is at +0x18, frees a node at each step, and loops. The nine `call 0x9984B0` instructions are the nine
// steps of the unrolled form, and the backwards jump at 0x923291 is the loop the unrolling came from.
//
// WHY THIS IS A SECOND HEADER RATHER THAN A PARAMETER OF owned_chain.hpp. That one's link is at +0x10 and its nodes own two buffers
// with an inline-or-heap test; this one's link is at +0x18 and it frees the node itself with no buffer test. **Same shape, different
// offset, and the offsets are what tell them apart** -- which is the rule this project applies to every pair of similar structures,
// and the reason both are recorded rather than merged.
#pragma once

#include <cstddef>

namespace lcns {

/** The link offset this chain uses, against owned_chain.hpp's +0x10. RE 0x92313C: `mov rax, [rax+0x18]`. */
constexpr std::size_t kDeepChainLink = 0x18;

/** The link read, isolated so the offset appears in one place. RE 0x92313C: `mov rax, [rax+0x18]`. */
template <typename Node>
Node* linkAt(Node* node) {
    return *reinterpret_cast<Node**>(reinterpret_cast<unsigned char*>(node) + kDeepChainLink);
}

/** RE 0x923110's walk, as the instructions express it: follow the link, release the node, repeat until null.
 *
 * `release` is a parameter rather than a recovered body because the module has thirty-five copies of this routine and they release
 * through the allocator, which this project CLASSIFIES rather than recovers -- re/CATEGORIES.md carries that, and the ledger grades
 * it SUBSTITUTED. What is recovered here is the walk, which is the part that carries the structure.
 *
 * The null test is at 0x923120 and the loop's back edge at 0x923291, so a null argument is a no-op and the walk continues while the
 * link is non-null.
 */
template <typename Node, typename Release>
void releaseDeepChain(Node* head, Release release) {
    while (head != nullptr) {              // RE 0x923120 and 0x923291
        Node* next = linkAt(head);         // RE 0x92313C: the link is read BEFORE the node is released
        release(head);                     // RE the nine `call 0x9984B0`
        head = next;
    }
}

static_assert(kDeepChainLink == 0x18, "RE 0x92313C");
static_assert(kDeepChainLink != 0x10, "owned_chain.hpp's link is at +0x10, and the offsets are what tell the two apart");

}  // namespace lcns
