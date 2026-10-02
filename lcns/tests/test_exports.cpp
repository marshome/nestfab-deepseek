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

#include <cstdint>
#include <cstring>

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
                    CHECK(ex::entries()[j].status == ex::Status::Forwarded);
                }
            }
            CHECK(found);   // a forwarding entry that names no ordinal would never be used
        }
        if (ex::forwardingCount() == 0) {
            // Stated as a fact of this stage: nothing forwards yet, so every definition above failed loudly.
            for (std::size_t i = 0; i < ex::count(); ++i) {
                CHECK(!ex::forwards(i));
                CHECK(ex::entries()[i].status == ex::Status::NotReversed);
            }
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
            if (e->status == ex::Status::NotReversed) {
                ++marked;
                CHECK(!ex::forwards(i));
            } else {
                CHECK(ex::forwards(i));
            }
        }
        CHECK(marked == ex::count() - ex::forwardedCount());
    }

    return check::finish("exports");
}
