// lcns/embedded.hpp -- original machine code kept inside the project, with the reason each piece is not reimplemented.
//
// WHY THIS EXISTS (round 355, on the user's instruction)
// -----------------------------------------------------
// The project is supposed to end up equivalent to libcns_dump_64.dll. Where a region has not been taken apart into C++
// yet, this header and its generated companions keep the ORIGINAL BYTES in the tree, so the gap is visible in code
// rather than only in a document, and so the original can act as the oracle a reimplementation is tested against.
//
// TWO STATUSES, decided mechanically by re/g_embed.py and never by hand:
//
//   Callable     -- the block contains no RIP-relative memory operand, no call or jump whose target lies outside the
//                   block, and no absolute address inside the image. Such a block is position-independent: an
//                   executable copy of its bytes behaves exactly as the original does, so tests may call it and
//                   compare it with a C++ reimplementation.
//
//   CommentOnly  -- one of those appears, and the reason names which. The bytes are still embedded (as data) and the
//                   disassembly is in re/EMBEDDED.md, but the project does not pretend it can run them: a relative
//                   call would land outside the copy, and a RIP-relative access would read the wrong address.
//
// HONESTY RULES THAT GO WITH THIS
//   * An embedded block is NOT "recovered code". It is the original binary, carried as a fallback and as a test
//     oracle. Calling it from library code would defeat the purpose of the reconstruction, so nothing under src/
//     except the tests and the table itself refers to it.
//   * re/check_embeddings.py re-reads the DLL and fails if any byte or hash drifts, so the embedded copies cannot
//     silently stop matching the binary they came from.
//   * A block being callable says nothing about the block being UNDERSTOOD; the registry keeps the note and the
//     reason, and re/EMBEDDED.md carries the listing for a reader to check.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {
namespace embedded {

// A pointer to an embedded original. Its real signature is whatever the block was called with; a caller casts to that,
// and the differential tests are where those casts live.
using RawFn = void (*)();

enum class Status {
    Callable,     // position-independent: an executable copy exists in gen_orig.S
    CommentOnly,  // bytes embedded as data; the reason says why it cannot be executed
};

struct Block {
    std::uintptr_t rva;          // address in libcns_dump_64.dll (ImageBase 0x6B4C0000)
    std::size_t size;            // bytes
    const char* symbol;          // lcns_orig_<rva>, defined by gen_orig.S when callable
    Status status;
    const char* reason;          // empty for Callable
    const char* note;            // what the block was read as doing
    const unsigned char* bytes;  // the original bytes, always present
    const char* sha256;          // hash of those bytes, checked against the DLL by re/check_embeddings.py
};

extern const Block kBlocks[];
extern const std::size_t kBlockCount;

// Addresses of the executable copies, in callable order. Defined by gen_table.cpp, which is the only translation unit
// that references the assembly symbols.
extern const RawFn kOrigTable[];
extern const std::size_t kOrigTableCount;

// --- helpers, implemented in src/embedded.cpp -----------------------------------------------------------------
const Block* find(std::uintptr_t rva);
Status statusOf(std::uintptr_t rva);
std::size_t callableCount();
std::size_t commentOnlyCount();
std::size_t embeddedBytes();
// The executable copy of a callable block as a callable pointer, or nullptr when the block is comment-only or unknown.
RawFn originalOf(std::uintptr_t rva);

}  // namespace embedded
}  // namespace lcns
