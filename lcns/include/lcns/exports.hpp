// lcns/exports.hpp -- the C ABI layer's runtime half: what each entry point is, and what happens when one is called.
//
// The original module exports 168 functions. This project defines all of them (see src/api_exports.cpp, generated), so a
// caller linking against it finds every name the original offers. What a definition DOES is a separate question, and it
// is answered per entry:
//
//   Forwarded    -- the behaviour has been recovered in C++; the definition calls that implementation.
//   NotReversed  -- it has not been recovered yet. The definition records the call and returns the documented neutral
//                   value for its return type (0, null or NaN) so the caller can tell failure from a result.
//
// Nothing here guesses. A not-reversed entry cannot return a plausible-looking wrong answer, and the diagnostic says
// which export was called and where its original code lives, so the gap is visible at the point of use rather than
// buried in a document. Every entry's original bytes are embedded in the project (re/g_embed.py embeds the export list)
// and re/check_embeddings.py keeps them equal to the module's -- that is what "the implementation agrees with the
// assembly" means for an entry that has no implementation yet.

#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {
namespace dll {
namespace exports {

enum class Status {
    Forwarded,    // the definition calls a recovered C++ implementation
    NotReversed,  // the definition reports the call and returns the documented neutral value
};

/** One entry point of the original module. */
struct Entry {
    const char* name;      // the label the module logs, or sub_XXXXX when it has none
    int ordinal0;          // the module exports each function twice, at adjacent ordinals
    int ordinal1;
    std::uint32_t rva;     // where the original code lives
    std::uint32_t size;    // how many bytes of it
    Status status;
    const char* note;      // the label's text, kept verbatim
};

/**
 * A recovered C++ implementation an entry point can forward to.
 *
 * Keyed by ORDINAL, not by name: the original module exports by ordinal (its export directory has NumberOfNames = 0) and
 * the names this project uses were recovered from the labels the functions log, so two entries can share a label.
 */
struct Forwarding {
    int ordinal0;
    void* implementation;
};

/** The table of every export, in the module's export-table order. */
const Entry* entries();
std::size_t count();

/**
 * The address of the definition for entry @p index, as a raw function pointer. The definitions are argument-independent
 * (they only report and return a constant), which is what makes it sound for a test to call all of them without knowing
 * their signatures.
 */
using RawFn = void (*)();
RawFn addressOf(std::size_t index);

/** Called by a definition whose behaviour has not been recovered. Records it; never guesses. */
void notReversed(std::size_t index);

/** How many such calls have been made, and which export was last. */
std::size_t notReversedCount();
const Entry* lastNotReversed();

/** How many entry points forward to a recovered implementation. */
std::size_t forwardedCount();
bool forwards(std::size_t index);

/**
 * The forwarding map itself, so a test can check its shape rather than take the count on trust: every entry must name an
 * ordinal that exists in the table, and `forwards()` must agree with the map for every index.
 */
const Forwarding* forwarding(std::size_t index);
std::size_t forwardingCount();

/** The original bytes of an entry point's code, straight from the embedded registry. */
struct OriginalBytes {
    const unsigned char* bytes;
    std::uint32_t size;
    const char* sha256;
};
OriginalBytes originalBytesOf(std::size_t index);

}  // namespace exports
}  // namespace dll
}  // namespace lcns
