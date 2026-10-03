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
#include "lcns/dll_layout.hpp"
#include "lcns/embedded.hpp"
#include "lcns/exports.hpp"
#include "lcns/exports_impl.hpp"
#include "lcns/launching_order.hpp"

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

        // GetSolution (0xB0A0): an identity over any pointer, including null.
        {
            int dummy = 0;
            CHECK(ex::impl::getSolutionIdentity(&dummy) == &dummy);
            CHECK(ex::impl::getSolutionIdentity(nullptr) == nullptr);
        }

        // sub_16CF0 (210/211): the same getter as GetPartUserString, without the logger call.
        {
            std::vector<unsigned char> obj(0x1C0, 0);
            const char* text = "another string";
            const std::uint64_t p = reinterpret_cast<std::uint64_t>(text);
            std::memcpy(obj.data() + 0x1B8, &p, 8);
            CHECK(ex::impl::getUserStringAt1B8(obj.data()) == text);
            CHECK(ex::impl::getUserStringAt1B8(obj.data()) == ex::impl::getPartUserString(obj.data()));
        }

        // sub_AFF0 (288/289): the stored byte is (arg != 0), and nothing else is written.
        {
            std::vector<unsigned char> obj(0x100, 0xAA);
            ex::impl::setByteAtF8(obj.data(), 1);
            CHECK(obj[0xF8] == 1u);
            ex::impl::setByteAtF8(obj.data(), 0);
            CHECK(obj[0xF8] == 0u);
            ex::impl::setByteAtF8(obj.data(), 256);
            CHECK(obj[0xF8] == 1u);
            ex::impl::setByteAtF8(obj.data(), -1);
            CHECK(obj[0xF8] == 1u);
            CHECK(obj[0xF7] == 0xAAu && obj[0xF9] == 0xAAu);
        }

        // sub_B000 (286/287): one double at +0x100 and one flag at +0xF9.
        {
            std::vector<unsigned char> obj(0x110, 0xAA);
            ex::impl::setDoubleAndFlag(obj.data(), 3, 5.5);
            double stored = 0.0;
            std::memcpy(&stored, obj.data() + 0x100, 8);
            CHECK(stored == 5.5);
            CHECK(obj[0xF9] == 1u);
            ex::impl::setDoubleAndFlag(obj.data(), 0, 0.0);
            std::memcpy(&stored, obj.data() + 0x100, 8);
            CHECK(stored == 0.0);
            CHECK(obj[0xF9] == 0u);
            CHECK(obj[0xF8] == 0xAAu);
        }

        // SetShearMode (offset 0x44)
        {
            std::vector<unsigned char> obj(0x300, 0xAA);
            ex::impl::setShearMode(obj.data(), 0x12345678);
            std::uint32_t got = 0;
            std::memcpy(&got, obj.data() + 0x44, 4);
            CHECK(got == 0x12345678u);
            ex::impl::setShearMode(obj.data(), -2);
            std::memcpy(&got, obj.data() + 0x44, 4);
            CHECK(got == 0xFFFFFFFEu);          // stored as a 32-bit value, not widened
        }

        // CNS_SetNoMixPreference (offset 0x18)
        {
            std::vector<unsigned char> obj(0x300, 0xAA);
            ex::impl::setNoMixPreference(obj.data(), 0x12345678);
            std::uint32_t got = 0;
            std::memcpy(&got, obj.data() + 0x18, 4);
            CHECK(got == 0x12345678u);
            ex::impl::setNoMixPreference(obj.data(), -2);
            std::memcpy(&got, obj.data() + 0x18, 4);
            CHECK(got == 0xFFFFFFFEu);          // stored as a 32-bit value, not widened
        }

        // CNS_SetNoSheetMixPreference (offset 0x1C)
        {
            std::vector<unsigned char> obj(0x300, 0xAA);
            ex::impl::setNoSheetMixPreference(obj.data(), 0x12345678);
            std::uint32_t got = 0;
            std::memcpy(&got, obj.data() + 0x1C, 4);
            CHECK(got == 0x12345678u);
            ex::impl::setNoSheetMixPreference(obj.data(), -2);
            std::memcpy(&got, obj.data() + 0x1C, 4);
            CHECK(got == 0xFFFFFFFEu);          // stored as a 32-bit value, not widened
        }

        // SetShearRepulseFromBorders (offset 0x58)
        {
            std::vector<unsigned char> obj(0x300, 0xAA);
            ex::impl::setShearRepulseFromBorders(obj.data(), 0x12345678);
            std::uint32_t got = 0;
            std::memcpy(&got, obj.data() + 0x58, 4);
            CHECK(got == 0x12345678u);
            ex::impl::setShearRepulseFromBorders(obj.data(), -2);
            std::memcpy(&got, obj.data() + 0x58, 4);
            CHECK(got == 0xFFFFFFFEu);          // stored as a 32-bit value, not widened
        }

        // UnLockLaunchingOrder (offset 0x244)
        {
            std::vector<unsigned char> obj(0x300, 0xAA);
            ex::impl::unlockLaunchingOrder(obj.data(), 0x12345678);
            std::uint32_t got = 0;
            std::memcpy(&got, obj.data() + 0x244, 4);
            CHECK(got == 0x12345678u);
            ex::impl::unlockLaunchingOrder(obj.data(), -2);
            std::memcpy(&got, obj.data() + 0x244, 4);
            CHECK(got == 0xFFFFFFFEu);          // stored as a 32-bit value, not widened
        }
        // SetLocalMaximumIterations (ord 84, offset 0x1FC)
        // **AND IT READS `Order` RATHER THAN A BYTE BUFFER AT +0x1FC.** The implementation now takes `Order*` -- the type the wrapper has always named -- so the
        // test asserts the FIELD. **The `memcpy` at a hand-written offset was the test doing the compiler's job**, and it is what let the carrier names survive:
        // a buffer cannot disagree with a signature.
        {
            lcns::Order order{};
            ex::impl::setLocalMaximumIterations(&order, 0x12345678);
            CHECK(order.maxIterations == 0x12345678u);
            ex::impl::setLocalMaximumIterations(&order, -2);
            CHECK(order.maxIterations == 0xFFFFFFFEu);   // a 32-bit store: the value is not widened
            // and the byte-level view agrees, which is the one thing the field cannot show
            std::uint32_t atOffset = 0;
            // **and a BYTE pointer, not a `void*`**: `void*` arithmetic is a GCC extension that warns, and the warning is the compiler asking which width the
            // offset is in. `reinterpret_cast<const unsigned char*>` answers it.
            std::memcpy(&atOffset, reinterpret_cast<const unsigned char*>(&order) + 0x1FC, 4);
            CHECK(atOffset == 0xFFFFFFFEu);
            // **AND THE FORWARD IS NOW REAL AND NOT JUST LISTED.** `kForwarding` named this ordinal before the wrapper dispatched, so `forwards(84)` was true
            // while the exported function still reported the ordinal to `notReversed` -- a list saying one thing and the code another. **The wrapper now calls
            // the implementation, so the two agree**, and this checks the agreement rather than the list.
            CHECK(ex::forwards(84u));
            CHECK(ex::forwardingCount() == 47u);
        }
        // The 14 are exactly the entries the hand-written map forwards to.
        CHECK(ex::forwardedCount() == 47u);
        for (std::size_t i = 0; i < ex::count(); ++i) {
            const ex::Entry* e = &ex::entries()[i];
            const bool expected = sameName(e->name, "GetNumberOfNestings") || sameName(e->name, "GetNumberOfNestedParts") ||
                                  sameName(e->name, "GetMultiplicity") || sameName(e->name, "GetPartUserString") ||
                                  sameName(e->name, "GetSolution") ||
                                  e->ordinal0 == 210 || e->ordinal0 == 288 || e->ordinal0 == 286 ||
                                  e->ordinal0 == 146 || e->ordinal0 == 188 || e->ordinal0 == 222 ||
                                  e->ordinal0 == 304 || e->ordinal0 == 76 ||
                                  e->ordinal0 == 84 || e->ordinal0 == 29 || e->ordinal0 == 144 || e->ordinal0 == 166 || e->ordinal0 == 182 || e->ordinal0 == 312 || e->ordinal0 == 330 || e->ordinal0 == 316 || e->ordinal0 == 336 || e->ordinal0 == 338 || e->ordinal0 == 334 || e->ordinal0 == 78 || e->ordinal0 == 212 || e->ordinal0 == 238 || e->ordinal0 == 73 || e->ordinal0 == 82 || e->ordinal0 == 270 || e->ordinal0 == 208 ||
                                  // round 537: the nine setters re/g_ready.py found ready
                                  e->ordinal0 == 86 || e->ordinal0 == 154 || e->ordinal0 == 128 || e->ordinal0 == 140 || e->ordinal0 == 150 || e->ordinal0 == 176 || e->ordinal0 == 298 || e->ordinal0 == 300 || e->ordinal0 == 246 ||
                                  // round 557: the build metadata, whose whole body is a logger call and one std::string data
                                  // pointer. They were never blocked -- the 256 function closure they appeared to carry was the
                                  // LOGGER's reachable graph, not their own need.
                                  e->ordinal0 == 88 || e->ordinal0 == 90 || e->ordinal0 == 92 ||
                                  // round 593: the two variant wrappers, which share the tail target 0x132E0 and
                                  // whose every callee on the path is now read
                                  e->ordinal0 == 196 || e->ordinal0 == 198 ||
                                  // round 598: two more of the variant family, whose targets 0x14A60 and 0xC1A0 are read.
                                  // Ordinal 204 is deliberately NOT here: its target 0x10CE0 has only its head read, and a
                                  // forwarding entry claims agreement with the assembly.
                                  e->ordinal0 == 200 || e->ordinal0 == 202;
            CHECK(ex::forwards(i) == expected);
        }
    }

    // ------------------------------- the object model, named here so it cannot drift out of the suite
    {
        // The container template first, because a name no test mentions is a name nobody checks.
        lcns::dll::RawVector<lcns::dll::NestingElement> empty{};
        empty.begin = nullptr;
        empty.end = nullptr;
        empty.capacity = nullptr;
        CHECK(empty.size() == 0u);
        CHECK(sizeof(lcns::dll::RawVector<lcns::dll::NestingElement>) == 24u);   // begin, end, capacity
        CHECK(sizeof(lcns::dll::RawVector<lcns::dll::NestedPartElement>) == 24u);

        CHECK(sizeof(lcns::dll::NestingElement) == 312);
        CHECK(sizeof(lcns::dll::NestedPartElement) == 120);
        // The assembly's constants are DERIVED from those sizes and pinned to the literals it actually uses.
        CHECK(lcns::dll::modularInverse(39) == 0x6F96F96F96F96F97ull);
        CHECK(lcns::dll::modularInverse(15) == 0xEEEEEEEEEEEEEEEFull);
        CHECK(offsetof(lcns::dll::SubObject, multiplicity) == 0x20);
        CHECK(offsetof(lcns::dll::SubObject, parts) == 0x28);
        CHECK(offsetof(lcns::dll::NestingOwner, sub) == 0x08);
        CHECK(offsetof(lcns::dll::NestingOwner, nestings) == 0x50);
        CHECK(offsetof(lcns::dll::PartObject, userString) == 0x1B8);
        CHECK(offsetof(lcns::dll::IntFieldCarrier, field18) == 0x18);
        CHECK(offsetof(lcns::dll::IntFieldCarrier, field1C) == 0x1C);
        CHECK(offsetof(lcns::dll::IntFieldCarrier, field44) == 0x44);
        CHECK(offsetof(lcns::dll::IntFieldCarrier, field58) == 0x58);
        CHECK(offsetof(lcns::dll::IntFieldCarrier, field1FC) == 0x1FC);
        CHECK(offsetof(lcns::dll::IntFieldCarrier, field244) == 0x244);
        CHECK(offsetof(lcns::dll::UnknownFlagCarrier, flagF8) == 0xF8);
        CHECK(offsetof(lcns::dll::UnknownFlagCarrier, flagF9) == 0xF9);
        CHECK(offsetof(lcns::dll::UnknownFlagCarrier, value100) == 0x100);

        // The structure and the raw bytes must agree: the same fixture the void* tests use, read through the model.
        std::vector<unsigned char> elements(3u * 312u, 0);
        std::vector<unsigned char> owner(0x68, 0);
        const std::uint64_t b = reinterpret_cast<std::uint64_t>(elements.data());
        const std::uint64_t e2 = b + elements.size();
        std::memcpy(owner.data() + 0x50, &b, 8);
        std::memcpy(owner.data() + 0x58, &e2, 8);
        CHECK(ex::impl::getNumberOfNestings(owner.data()) == 3u);
        CHECK(reinterpret_cast<lcns::dll::NestingOwner*>(owner.data())->nestings.size() == 3u);
        // A malformed container is where the original's multiply and a division differ; the model must keep the original.
        const std::uint64_t e3 = b + 312u;
        std::memcpy(owner.data() + 0x58, &e3, 8);
        CHECK(reinterpret_cast<lcns::dll::NestingOwner*>(owner.data())->nestings.size() == 1u);
    }

    // ------------------------------------- GetPartWithBadGeometry (ordinal 29), from its own thirteen instructions
    {
        // The original cannot be executed from the embedded copy -- it calls the logger with a RIP-relative label -- so
        // this is a behavioural test: the decoded offsets and the decoded condition, checked against hand-computed
        // expectations.
        std::vector<unsigned char> object(0xA8, 0x5A);
        std::uint32_t status = 0;
        std::memcpy(object.data() + 0x4C, &status, sizeof(status));
        const void* geom = reinterpret_cast<const void*>(0x1234);
        std::memcpy(object.data() + 0xA0, &geom, sizeof(geom));
        CHECK(ex::impl::getPartWithBadGeometry(object.data()) == nullptr);      // status 0 returns null
        status = 2;
        std::memcpy(object.data() + 0x4C, &status, sizeof(status));
        CHECK(ex::impl::getPartWithBadGeometry(object.data()) == nullptr);      // and so does any status but 1
        status = 1;
        std::memcpy(object.data() + 0x4C, &status, sizeof(status));
        CHECK(ex::impl::getPartWithBadGeometry(object.data()) == geom);         // status 1 returns +0xA0
        const void* nothing = nullptr;
        std::memcpy(object.data() + 0xA0, &nothing, sizeof(nothing));
        CHECK(ex::impl::getPartWithBadGeometry(object.data()) == nullptr);      // even when that field is null
        // the carrier's offsets are asserted by the compiler too, and named here so the model is in the suite
        CHECK(offsetof(lcns::dll::BadGeometryCarrier, status) == 0x4C);
        CHECK(offsetof(lcns::dll::BadGeometryCarrier, geometry) == 0xA0);
    }

        CHECK(sizeof(lcns::dll::Element48) == 48);
        CHECK(lcns::dll::modularInverse(3) == 0xAAAAAAAAAAAAAAABull);

        CHECK(sizeof(lcns::dll::Element216) == 216);
        CHECK(lcns::dll::modularInverse(27) == 0x84BDA12F684BDA13ull);

        // **ONLY THE TWO SLOTS THE IMPLEMENTATIONS SUBTRACT.** The other six offsets were read out of `movsd xmm0, [rsp + ...]` arithmetic in the two
        // `windowSpan*` functions, whose locals live on the stack (`0x526189 lea rsi, [rsp + 0xa0]`), **so they were never members of anything.**
        CHECK(offsetof(lcns::dll::WindowSlots, slot08) == 0x08);   // the low value windowSpanLength subtracts
        CHECK(offsetof(lcns::dll::WindowSlots, slot10) == 0x10);   // and the one windowSpanHeight subtracts
             // read from the code, writer not yet traced

        CHECK(offsetof(lcns::dll::CachedBoxCarrier, initialised) == 0x100);   // RE 0x4F920B
        CHECK(offsetof(lcns::dll::CachedBoxCarrier, box) == 0x108);           // RE 0x4F9217

    // ------------------- the mode setters, each against its own decoded offset on `Order` itself
    // **THESE USED TO RUN AGAINST `OptionFlagCarrier`, WHICH IS A SECOND DESCRIPTION OF FIELDS `Order` HAS.** Each byte is now read through the name the export
    // that writes it gave the field, so a rename that broke the mapping would fail here rather than pass.
    {
        // **NOISE IN THE FIELDS UNDER TEST AND NOT A memset OVER THE WHOLE OBJECT.** Order has non-trivial members, so memset is -Wclass-memaccess and the gate
        // fails on warnings -- and it would also be wrong: the noise is only meaningful where a write could land.
        lcns::Order order{};
        order.fillLastNestingStrategy = true; order.floatingMode = true; order.originPackingMode = true;
        order.field1C = 0x5A5A5A5Au; order.shear = 0x5A5A5A5Au; order.shearCorner = 0x5A5A5A5Au;

        lcns::dll::exports::impl::setFillLastNestingStrategy(&order, 7);
        CHECK(order.fillLastNestingStrategy == 1);          // RE 0xDDA9 stores the truth value, not the number
        lcns::dll::exports::impl::setFillLastNestingStrategy(&order, 0);
        CHECK(order.fillLastNestingStrategy == 0);

        lcns::dll::exports::impl::setPartCommonCutMode(&order, -1);
        CHECK((order.field1C & 0xFFu) == 1u);               // RE 0xDE69 writes the LOW BYTE of a 32-bit field
        lcns::dll::exports::impl::setPartCommonCutMode(&order, 0);
        CHECK((order.field1C & 0xFFu) == 0u);

        lcns::dll::exports::impl::setFloatingMode(&order, 3);
        CHECK(order.floatingMode == 1);
        lcns::dll::exports::impl::setFloatingMode(&order, 0);
        CHECK(order.floatingMode == 0);

        lcns::dll::exports::impl::setOriginPackingMode(&order, 1);
        CHECK(order.originPackingMode == 1);
        lcns::dll::exports::impl::setOriginPackingMode(&order, 0);
        CHECK(order.originPackingMode == 0);

        lcns::dll::exports::impl::setPartialShearMode(&order, 12345);
        CHECK(order.shear == 12345u);                       // RE 0xDE0A
        CHECK(order.shearCorner == 12345u);                 // RE 0xDE07: both take the value, not its truth

        // **AND THE FIELDS THE FOUR FLAG SETTERS MUST NOT TOUCH.** `shear` and `shearCorner` are thirty-two bits, so a byte write aimed at a neighbouring flag
        // would land inside them -- which is exactly the damage the carrier's byte layout could hide.
        CHECK(order.shear == 12345u && order.shearCorner == 12345u);

        CHECK(offsetof(lcns::Order, field1C) == 0x1C);
        CHECK(offsetof(lcns::Order, floatingMode) == 0x20);
        CHECK(offsetof(lcns::Order, originPackingMode) == 0x21);
        CHECK(offsetof(lcns::Order, fillLastNestingStrategy) == 0x40);
        CHECK(offsetof(lcns::Order, shear) == 0x44);
        CHECK(offsetof(lcns::Order, shearCorner) == 0x48);
    }

    // ------------------- second sweep: seven more exports, each against its decoded offset
    {
        lcns::Order flags{};
        flags.evaluateIntermediateNestingsAsLast = true;
        flags.reorganizeBiggestPartNearOrigin = true;
        flags.reorganizeLongestPartNearOrigin = true;
        lcns::dll::exports::impl::setEvaluateIntermediateNestingsAsLast(&flags, 5);
        CHECK(flags.evaluateIntermediateNestingsAsLast == 1);                       // RE 0x1045F stores the truth value
        lcns::dll::exports::impl::setEvaluateIntermediateNestingsAsLast(&flags, 0);
        CHECK(flags.evaluateIntermediateNestingsAsLast == 0);
        lcns::dll::exports::impl::setReorganizeBiggestPartNearOrigin(&flags, -2);
        CHECK(flags.reorganizeBiggestPartNearOrigin == 1);                       // RE 0x1048F
        lcns::dll::exports::impl::setReorganizeLongestPartNearOrigin(&flags, 9);
        CHECK(flags.reorganizeLongestPartNearOrigin == 1);                       // RE 0x104BF
        CHECK(offsetof(lcns::Order, reorganizeBiggestPartNearOrigin) == 0x22);
        CHECK(offsetof(lcns::Order, reorganizeLongestPartNearOrigin) == 0x23);
        CHECK(offsetof(lcns::Order, evaluateIntermediateNestingsAsLast) == 0x41);

        lcns::dll::HoleForceCarrier part{};
        std::memset(&part, 0x5A, sizeof(part));
        lcns::dll::exports::impl::forcePartInsideHole(&part);
        CHECK(part.insideHole == 1);                    // RE 0xC627
        CHECK(part.something == 0);                     // RE 0xC62E
        CHECK(offsetof(lcns::dll::HoleForceCarrier, insideHole) == 0x20A);
        CHECK(offsetof(lcns::dll::HoleForceCarrier, something) == 0x20B);

        lcns::dll::SolverOptionCarrier options{};
        std::memset(&options, 0x5A, sizeof(options));
        lcns::dll::exports::impl::setObjective(&options, 4321);
        CHECK(options.objective == 4321);               // RE 0xCEE3 stores the integer, not its truth value
        lcns::dll::exports::impl::setShearGap(&options, 2.5);
        CHECK(options.shearGap == 2.5);                 // RE 0xCF0D
        CHECK(offsetof(lcns::dll::SolverOptionCarrier, objective) == 0x08);
        CHECK(offsetof(lcns::dll::SolverOptionCarrier, shearGap) == 0x50);

        // three 48-byte elements: the count must be three, which only holds if the stride is 48 and not 16
        std::vector<unsigned char> storage(3 * 48, 0);
        unsigned char owner[16];
        const std::uintptr_t begin = reinterpret_cast<std::uintptr_t>(storage.data());
        const std::uintptr_t end = begin + storage.size();
        std::memcpy(owner, &begin, sizeof(begin));
        std::memcpy(owner + 8, &end, sizeof(end));
        CHECK(lcns::dll::exports::impl::noFitGetNumberOfExternalPolygons(owner) == 3u);
        CHECK(lcns::dll::modularInverse(3) == 0xAAAAAAAAAAAAAAABull);   // the multiplier in RE 0x89EB
    }

    // ------------------- SetLocalEngine and SetLocalMaximumThreads, both read whole
    {
        lcns::dll::LocalEngineCarrier local{};
        std::memset(&local, 0x5A, sizeof(local));
        lcns::dll::exports::impl::setLocalEngine(&local, 0);
        CHECK(local.engineLo == 1);                     // bit zero is 0, so its complement is 1 (RE 0xD38B)
        CHECK(local.engineHi == 1);                     // bit one is 0 too
        lcns::dll::exports::impl::setLocalEngine(&local, 1);
        CHECK(local.engineLo == 0);                     // bit zero is 1, complement 0
        CHECK(local.engineHi == 1);
        lcns::dll::exports::impl::setLocalEngine(&local, 2);
        CHECK(local.engineLo == 1);
        CHECK(local.engineHi == 0);                     // bit one is 1, complement 0
        lcns::dll::exports::impl::setLocalEngine(&local, 3);
        CHECK(local.engineLo == 0);
        CHECK(local.engineHi == 0);
        CHECK(offsetof(lcns::dll::LocalEngineCarrier, engineLo) == 0x200);
        CHECK(offsetof(lcns::dll::LocalEngineCarrier, engineHi) == 0x201);

        // the recovered logic around the platform number, over a grid: floor at one, then the smaller of the two
        CHECK(lcns::dll::exports::impl::clampMaximumThreads(0u, 0) == 1u);      // zero becomes one (RE 0xB5B79)
        CHECK(lcns::dll::exports::impl::clampMaximumThreads(0u, 4) == 1u);      // min(1, 4)
        CHECK(lcns::dll::exports::impl::clampMaximumThreads(8u, 0) == 8u);      // the argument-zero branch (RE 0xD3E2)
        CHECK(lcns::dll::exports::impl::clampMaximumThreads(8u, 3) == 3u);      // min(8, 3), RE 0xD3D2
        CHECK(lcns::dll::exports::impl::clampMaximumThreads(8u, 12) == 8u);     // min(8, 12) keeps the platform value
        CHECK(lcns::dll::exports::impl::clampMaximumThreads(1u, 1) == 1u);
        for (unsigned hw = 0; hw <= 16u; ++hw) {
            for (int want = 0; want <= 16; ++want) {
                const unsigned expected = (want == 0) ? ((hw == 0u) ? 1u : hw)
                                                      : ((((hw == 0u) ? 1u : hw) > static_cast<unsigned>(want))
                                                             ? static_cast<unsigned>(want)
                                                             : ((hw == 0u) ? 1u : hw));
                CHECK(lcns::dll::exports::impl::clampMaximumThreads(hw, want) == expected);
            }
        }
    }

    // ------------------- the module switch, whose whole closure is sixteen bytes
    {
        lcns::dll::exports::impl::setModuleSwitch(0);
        CHECK(lcns::dll::exports::impl::moduleSwitch() == 0);
        lcns::dll::exports::impl::setModuleSwitch(7);
        CHECK(lcns::dll::exports::impl::moduleSwitch() == 1);    // any non-zero becomes exactly one (RE 0xAFE2)
        lcns::dll::exports::impl::setModuleSwitch(-1);
        CHECK(lcns::dll::exports::impl::moduleSwitch() == 1);
        lcns::dll::exports::impl::setModuleSwitch(0);
        CHECK(lcns::dll::exports::impl::moduleSwitch() == 0);
    }

    // ------------------- ordinal 208: a std::string assignment at +0x1B8
    {
        // A std::string has to live at +0x1B8 for this to be the same operation the original performs, so the test builds
        // exactly that: an object large enough, with a std::string at the offset the assembly names.
        alignas(std::string) unsigned char object[0x1B8 + sizeof(std::string) + 0x40];
        std::memset(object, 0, sizeof(object));
        auto* holder = new (object + 0x1B8) std::string();
        lcns::dll::exports::impl::setUserStringAt1B8(object, "hello");
        CHECK(holder->size() == 5);
        CHECK(*holder == "hello");
        lcns::dll::exports::impl::setUserStringAt1B8(object, "");
        CHECK(holder->empty());
        const char* longText = "a much longer string that will not fit in the small buffer at all";
        lcns::dll::exports::impl::setUserStringAt1B8(object, longText);
        CHECK(holder->size() == std::strlen(longText));                 // the assignment replaces rather than appends
        CHECK(holder->compare(0, 4, "a mu") == 0);
        lcns::dll::exports::impl::setUserStringAt1B8(object, nullptr);
        CHECK(holder->empty());                      // a null pointer is treated as the empty string
        holder->~basic_string();
        CHECK(offsetof(lcns::dll::UserStringHolder, data) == 0x00);
        CHECK(offsetof(lcns::dll::UserStringHolder, length) == 0x08);
        CHECK(offsetof(lcns::dll::UserStringHolder, smallBuffer) == 0x10);
    }


    // ------------------- the nine setters (round 537), every store against its RE address
    //
    // The offsets come from lcns/launching_order.hpp by FIELD NAME, never as literals, and each reader has the width of the
    // field it reads. Both halves of that matter and both were learned here: the block was first written against bare
    // offsets with a 4-byte reader, so when the header's widths changed it silently compared the wrong half of an 8-byte
    // field and six checks failed at once. `dword`, `byte` and `dbl` take a FIELD, so the compiler moves the check when the
    // layout moves.
    {
        using Order = lcns::dll::LaunchingOrderLayout;
        std::vector<unsigned char> order(sizeof(Order), 0xA5);
        auto byte = [&order](std::size_t offset) { return order[offset]; };
        auto dword = [&order](std::size_t offset) {
            std::uint32_t value = 0;
            std::memcpy(&value, order.data() + offset, sizeof(value));
            return value;
        };
        auto dbl = [&order](std::size_t offset) {
            double value = 0.0;
            std::memcpy(&value, order.data() + offset, sizeof(value));
            return value;
        };
        constexpr std::size_t kOrigin = offsetof(Order, origin);
        constexpr std::size_t kMultiplicityPreference = offsetof(Order, multiplicityPreference);
        constexpr std::size_t kCommonCutSafetyGiven = offsetof(Order, commonCutSafetyPreferenceGiven);
        constexpr std::size_t kCommonCutSafety = offsetof(Order, commonCutSafetyPreference);
        constexpr std::size_t kCommonCutCuttingGiven = offsetof(Order, commonCutCuttingPreferenceGiven);
        constexpr std::size_t kCommonCutCutting = offsetof(Order, commonCutCuttingPreference);
        constexpr std::size_t kMultiTorchGiven = offsetof(Order, multiTorchCuttingPreferenceGiven);
        constexpr std::size_t kMultiTorchPositive = offsetof(Order, multiTorchCuttingPreferencePositive);
        constexpr std::size_t kMultiTorch = offsetof(Order, multiTorchCuttingPreference);
        constexpr std::size_t kAutomaticStop = offsetof(Order, automaticStop);
        constexpr std::size_t kSheetOriginGiven = offsetof(Order, specificSheetOriginGiven);
        constexpr std::size_t kSheetOrigin = offsetof(Order, specificSheetOrigin);
        constexpr std::size_t kSheetObjectiveGiven = offsetof(Order, specificSheetObjectiveGiven);
        constexpr std::size_t kSheetObjective = offsetof(Order, specificSheetObjective);
        constexpr std::size_t kMarkGiven = offsetof(Order, markModeGiven);
        constexpr std::size_t kMarkFirst = offsetof(Order, markModeFirst);
        constexpr std::size_t kMarkSecond = offsetof(Order, markModeSecond);

        // The offsets the names resolve to, asserted once so a layout edit is visible in one place.
        CHECK(kOrigin == 0x00C);                     // RE 0xD119
        CHECK(kAutomaticStop == 0x240);              // RE 0xE0D9
        CHECK(kCommonCutSafety == 0x06C);            // RE 0xEA0D
        CHECK(kMultiplicityPreference == 0x010);     // RE 0xD26A, a double
        CHECK(kMarkFirst == 0x0E8);                  // RE 0x189FA, a double

        // RE 0xD119: SetOrigin (86) writes the dword at +0x0C.
        ex::impl::setOrigin_0D050(order.data(), 7);
        CHECK(dword(kOrigin) == 7u);
        // RE 0xED59 and 0xED60: SetCommonCutCuttingPreference (154).
        std::memset(order.data(), 0, order.size());
        ex::impl::setCommonCutCuttingPreference_0EC90(order.data(), 11);
        CHECK(byte(kCommonCutCuttingGiven) == 1);
        CHECK(dword(kCommonCutCutting) == 11u);
        // RE 0xE0D9: SetAutomaticStop (140) writes the mode 0x22A20 reads.
        std::memset(order.data(), 0, order.size());
        ex::impl::setAutomaticStop_0E010(order.data(), 2);
        CHECK(dword(kAutomaticStop) == 2u);
        // RE 0xEA09 and 0xEA0D: SetCommonCutSafetyPreference (150).
        std::memset(order.data(), 0, order.size());
        ex::impl::setCommonCutSafetyPreference_0E940(order.data(), 13);
        CHECK(byte(kCommonCutSafetyGiven) == 1);
        CHECK(dword(kCommonCutSafety) == 13u);
        // RE 0xF225, 0xF22C and 0xF233: SetMultiTorchCuttingPreference (176). **THE POSITIVE BYTE COMES FROM THE THIRD ARGUMENT AND NOT FROM THE VALUE** --
        // 0xF140 is `mov ebp, r8d` and 0xF22C is `setg byte [rsi + 0xa0]`. **The two calls below differ ONLY in the flag**, so a port that read the value
        // instead would pass the first and fail the second.
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiTorchCuttingPreference_0F130(order.data(), 5, 5);
        CHECK(byte(kMultiTorchGiven) == 1);
        CHECK(byte(kMultiTorchPositive) == 1);       // the flag is positive
        CHECK(dword(kMultiTorch) == 5u);             // the value is stored whatever the flag says
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiTorchCuttingPreference_0F130(order.data(), 5, 0);
        CHECK(byte(kMultiTorchGiven) == 1);          // unconditional, RE 0xF225
        CHECK(byte(kMultiTorchPositive) == 0);       // **setg reads the FLAG, and 5 > 0 would have said 1**
        CHECK(dword(kMultiTorch) == 5u);
        // RE 0x13F02 and 0x13F09: SetSpecificSheetOrigin (298).
        std::memset(order.data(), 0, order.size());
        ex::impl::setSpecificSheetOrigin_13E30(order.data(), 17);
        CHECK(byte(kSheetOriginGiven) == 1);
        CHECK(dword(kSheetOrigin) == 17u);
        // RE 0x140B2 and 0x140B9: SetSpecificSheetObjective (300).
        std::memset(order.data(), 0, order.size());
        ex::impl::setSpecificSheetObjective_13FE0(order.data(), 19);
        CHECK(byte(kSheetObjectiveGiven) == 1);
        CHECK(dword(kSheetObjective) == 19u);
        // RE 0x189FA, 0x18A09 and 0x18A10: SetMarkMode (246) takes two doubles and a flag.
        std::memset(order.data(), 0, order.size());
        ex::impl::setMarkMode_188D0(order.data(), 0, -1.5, 2.5);
        CHECK(dbl(kMarkFirst) == -1.5);
        CHECK(byte(kMarkGiven) == 0);                // setne
        CHECK(dbl(kMarkSecond) == 2.5);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMarkMode_188D0(order.data(), 3, 0.0, 0.0);
        CHECK(byte(kMarkGiven) == 1);
        // RE 0x9AD6D8 (0.25), 0x9AD6E0 (0.05), 0x9AD6E8 (0.001) and 0x9AD6D0 (2.0): the four constants
        // CNS_SetMultiplicityPreference (128) chooses between, and the default when nothing matches.
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiplicityPreference_0D1A0(order.data(), 0);
        CHECK(dbl(kMultiplicityPreference) == 0.25);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiplicityPreference_0D1A0(order.data(), 1);
        CHECK(dbl(kMultiplicityPreference) == 0.001);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiplicityPreference_0D1A0(order.data(), 3);
        CHECK(dbl(kMultiplicityPreference) == 0.05);
        std::memset(order.data(), 0, order.size());
        ex::impl::setMultiplicityPreference_0D1A0(order.data(), 4);
        CHECK(dbl(kMultiplicityPreference) == 2.0);
    }

    // ---------------------------------------------------------------- the build metadata (round 557)
    //
    // Three exports whose body is a logger call and one load, so their evidence is entirely in the disassembly: the global
    // each reads, the std::string it points at, and the bytes of that string's data in the image. The address of every step
    // is in the comments beside the implementation.
    {
        // RE 0xB470, and RE 0xB1F410 is where "Jun 28 2019" sits as the string's data.
        CHECK(std::string(lcns::dll::exports::impl::getBuildDate()) == "Jun 28 2019");
        // RE 0xB450, and RE 0xB1F430 holds "5.0"; the declared return is int, so the low byte is the character '5'.
        CHECK(lcns::dll::exports::impl::getMajorVersion() == '5');
        // RE 0xB490: the std::string at 0x6BFDF3C0 is EMPTY in the image, so the value is produced at load time. nullptr is
        // the documented unknown, and this check exists so that "unknown" stays distinguishable from "recovered as empty".
        CHECK(lcns::dll::exports::impl::getBuildVersion() == nullptr);
    }

    return check::finish("exports");
}

