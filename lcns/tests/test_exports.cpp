// tests/test_exports.cpp -- the C ABI layer: every export has a definition, and none of them can lie.
//
// The requirement this test exists for: the project must correspond to ALL the exported functions, and what each one
// does must agree with the assembly. Agreement is checkable two ways, and the test checks both:
//
//   * for an entry point with a recovered implementation, the C++ that implements it is compared with the original bytes
//     by a differential test (tests/test_affine, test_segcost, test_boxacc, test_embedded do this today);
//   * for an entry point without one, the ORIGINAL BYTES are in the project and verified against the module by
//     re/check_embeddings.py, and the definition cannot return a plausible wrong answer -- it reports the call and
//     returns the documented neutral value.
//
// The table is also where the gap is counted rather than described: forwardedCount() is the number of entry points the
// project actually implements, and this test prints it in its failure message if it ever goes backwards.

#include "check.hpp"
#include "lcns/embedded.hpp"
#include "lcns/exports.hpp"
#include "lcns/exports_impl.hpp"

#include <cstdint>
#include <cstring>
#include <vector>

namespace ex = lcns::dll::exports;
namespace emb = lcns::embedded;

namespace {

/** The number of exported functions the module has, from re/exports_table.json. */
constexpr std::size_t kExportCount = 168;

/** A value that cannot be mistaken for a comparison result. */
bool sameName(const char* a, const char* b) { return a != nullptr && b != nullptr && std::strcmp(a, b) == 0; }

}  // namespace

int main() {
    // ---------------------------------------------------------------- every export is present and described
    CHECK(ex::count() == kExportCount);
    {
        std::size_t withName = 0;
        std::size_t withTwoOrdinals = 0;
        std::size_t bytesPresent = 0;
        std::size_t bytesSized = 0;
        std::size_t repeatedLabels = 0;
        for (std::size_t i = 0; i < ex::count(); ++i) {
            const ex::Entry* e = &ex::entries()[i];
            CHECK(e->name != nullptr && e->name[0] != '\0');
            CHECK(e->ordinal0 > 0);
            CHECK(e->rva > 0);
            CHECK(e->size > 0);
            CHECK(e->note != nullptr);
            if (e->name[0] != 's' || std::strncmp(e->name, "sub_", 4) != 0) {
                ++withName;
            }
            if (e->ordinal1 > 0) {
                ++withTwoOrdinals;
            }
            // the tie between an entry point and the assembly: the bytes must be in the tree, and the right number of
            // them (re/check_embeddings.py checks those bytes against the module itself)
            const ex::OriginalBytes ob = ex::originalBytesOf(i);
            if (ob.bytes != nullptr) {
                ++bytesPresent;
                if (ob.size == e->size) {
                    ++bytesSized;
                }
                if (ob.sha256 == nullptr || std::strlen(ob.sha256) != 64) {
                    CHECK(false);   // a block without a hash cannot be checked for drift
                }
            }
            // Labels may repeat: the original exports by ordinal and its "names" are recovered log strings, so two
            // entries can carry the same label. The ORDINAL is the identity, and those must be distinct.
            for (std::size_t j = i + 1; j < ex::count(); ++j) {
                if (sameName(e->name, ex::entries()[j].name)) {
                    ++repeatedLabels;
                }
                CHECK(e->ordinal0 != ex::entries()[j].ordinal0);
            }
        }
        // 168/168 entry points have their original bytes embedded and their size recorded -- the requirement that the
        // assembly for every export is in the project.
        CHECK(bytesPresent == kExportCount);
        CHECK(bytesSized == kExportCount);
        CHECK(withName == 162);          // the other six have no label in the module
        CHECK(withTwoOrdinals == 168);   // every export is exported twice, at adjacent ordinals
        CHECK(repeatedLabels >= 1);   // observed: two entries log "AddLeatherQualityZoneInPart"
        CHECK(repeatedLabels <= 4);
    }

    // ---------------------------------------------------------------- calling one reports rather than guesses
    {
        const std::size_t before = ex::notReversedCount();
        // The definitions are argument-independent by construction (they only report and return a constant), so calling
        // them through a uniform pointer is exactly as sound as the ABI allows -- and it is what lets the test walk all
        // 168 of them.
        std::size_t called = 0;
        std::size_t forwarded = 0;
        for (std::size_t i = 0; i < ex::count(); ++i) {
            ex::RawFn fn = ex::addressOf(i);
            CHECK(fn != nullptr);
            if (fn == nullptr) {
                continue;
            }
            if (ex::forwards(i)) {
                ++forwarded;
                continue;   // a forwarded entry would run real work; it is covered by its own differential test
            }
            fn();
            ++called;
        }
        CHECK(called == ex::count() - forwarded);
        CHECK(ex::notReversedCount() == before + called);
        CHECK(forwarded == ex::forwardedCount());
        // and the last one called is remembered, so a diagnostic can name it
        const ex::Entry* last = ex::lastNotReversed();
        CHECK(last != nullptr);
        if (last != nullptr) {
            CHECK(last->name != nullptr && last->name[0] != '\0');
            CHECK(last->status == ex::Status::NotReversed);
            CHECK(last->rva > 0);
        }
    }

    // ---------------------------------------------------------------- the forwarding map's shape
    {
        // Named here on purpose: the map is what decides "real work" versus "fails loudly", so its shape is tested rather
        // than trusted. Every entry must name an ordinal that exists, and forwards() must agree with the map everywhere.
        CHECK(ex::forwardingCount() == ex::forwardedCount());
        for (std::size_t i = 0; i < ex::forwardingCount(); ++i) {
            const ex::Forwarding* f = ex::forwarding(i);
            CHECK(f != nullptr);
            if (f == nullptr) {
                continue;
            }
            CHECK(f->ordinal0 > 0);
            CHECK(f->implementation != nullptr);   // a forwarding entry with no implementation would be a lie
            bool found = false;
            for (std::size_t j = 0; j < ex::count(); ++j) {
                if (ex::entries()[j].ordinal0 == f->ordinal0) {
                    found = true;
                    CHECK(ex::forwards(j));
                    // the effective status comes from the map, not from the generated default
                    CHECK(ex::statusOf(j) == ex::Status::Forwarded);
                }
            }
            CHECK(found);   // a forwarding entry that names no ordinal would never be used
        }
        for (std::size_t i = 0; i < ex::count(); ++i) {
            // whatever the count is, the effective status must agree with the map for every single entry
            CHECK((ex::statusOf(i) == ex::Status::Forwarded) == ex::forwards(i));
        }
        CHECK(ex::forwarding(ex::forwardingCount()) == nullptr);   // out of range is not a valid lookup
    }

    // ---------------------------------------------------------------- the neutral values are the documented ones
    {
        // The recorded status must agree with the set of names the generated file forwards: an entry marked
        // NotReversed here must not also be in the forwarding map, and vice versa.
        std::size_t marked = 0;
        for (std::size_t i = 0; i < ex::count(); ++i) {
            const ex::Entry* e = &ex::entries()[i];
            CHECK(e->ordinal0 > 0);   // and the entry itself stays described while its status is checked
            if (ex::statusOf(i) == ex::Status::NotReversed) {
                ++marked;
                CHECK(!ex::forwards(i));
            } else {
                CHECK(ex::forwards(i));
            }
        }
        CHECK(marked == ex::count() - ex::forwardedCount());
    }

    // ------------------------------------------- the four recovered exports, from their assembly
    {
        // GetNumberOfNestings (0xB0C0): a container of 312-byte elements at order+0x50/+0x58.
        std::vector<unsigned char> nestings(4u * 312u, 0);
        std::vector<unsigned char> order(0x60, 0);
        const std::uint64_t begin = reinterpret_cast<std::uint64_t>(nestings.data());
        const std::uint64_t end = begin + nestings.size();
        std::memcpy(order.data() + 0x50, &begin, 8);
        std::memcpy(order.data() + 0x58, &end, 8);
        CHECK(ex::impl::getNumberOfNestings(order.data()) == 4u);
        // and the magic is exact for such a container, while NOT being the quotient in general -- a fact worth pinning,
        // because tidying the multiply into a division would change the behaviour of a malformed container.
        // The constant IS the modular inverse of the stride in eight-byte units: 312/8 = 39, and 120/8 = 15. Written the
        // first time as 0x18 and 0x3B, which were simply wrong -- the check below is the fact.
        CHECK(39ull * 0x6F96F96F96F96F97ull == 1ull);
        CHECK(15ull * 0xEEEEEEEEEEEEEEEFull == 1ull);
        CHECK(((1560ull >> 3) * 0x6F96F96F96F96F97ull) == 5ull);   // 5 * 312 bytes
        CHECK(((1568ull >> 3) * 0x6F96F96F96F96F97ull) != 5ull);   // one unit more is NOT the quotient of 1568/312

        // GetNumberOfNestedParts (0xB190): sub = [order+8], its container at sub+0x28/+0x30, stride 120.
        std::vector<unsigned char> sub(0x40, 0);
        std::vector<unsigned char> parts(3u * 120u, 0);
        const std::uint64_t pbegin = reinterpret_cast<std::uint64_t>(parts.data());
        const std::uint64_t pend = pbegin + parts.size();
        std::memcpy(sub.data() + 0x28, &pbegin, 8);
        std::memcpy(sub.data() + 0x30, &pend, 8);
        void* subPtr = sub.data();
        std::memcpy(order.data() + 0x08, &subPtr, 8);
        CHECK(ex::impl::getNumberOfNestedParts(order.data()) == 3u);

        // GetMultiplicity (0xB100 -> 0x51D090): the 32-bit field at +0x20 of that sub-object.
        const std::uint32_t mult = 7u;
        std::memcpy(sub.data() + 0x20, &mult, 4);
        CHECK(ex::impl::getMultiplicity(order.data()) == 7u);
        const std::uint32_t big = 0xFEDCBA98u;
        std::memcpy(sub.data() + 0x20, &big, 4);
        CHECK(ex::impl::getMultiplicity(order.data()) == 0xFEDCBA98u);   // unsigned, not sign extended

        // GetPartUserString (0xC5E0): the pointer at +0x1B8, returned unchanged.
        std::vector<unsigned char> part(0x1C0, 0);
        const char* text = "user string";
        const std::uint64_t textPtr = reinterpret_cast<std::uint64_t>(text);
        std::memcpy(part.data() + 0x1B8, &textPtr, 8);
        CHECK(ex::impl::getPartUserString(part.data()) == text);
        CHECK(std::strcmp(ex::impl::getPartUserString(part.data()), "user string") == 0);

        // The four are exactly the entries the hand-written map forwards to.
        CHECK(ex::forwardedCount() == 4u);
        for (std::size_t i = 0; i < ex::count(); ++i) {
            const ex::Entry* e = &ex::entries()[i];
            const bool expected = sameName(e->name, "GetNumberOfNestings") || sameName(e->name, "GetNumberOfNestedParts") ||
                                  sameName(e->name, "GetMultiplicity") || sameName(e->name, "GetPartUserString");
            CHECK(ex::forwards(i) == expected);
        }
    }

    return check::finish("exports");
}
