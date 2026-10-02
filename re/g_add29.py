# -*- coding: utf-8 -*-
"""Land export ordinal 29: GetPartWithBadGeometry.

Read whole in round 431, thirteen instructions and no calls but the logger:

    0B515  rbx = rcx                     ; the object
    0B518  lea rcx, [rip + ...]; call 0x64AEA0   ; the logger, whose default path does nothing
    0B524  edx = dword [rbx + 0x4C]      ; a 32-bit status field
    0B527  eax = 0                       ; the default return is null
    0B529  cmp edx, 1 ; jne 0B535        ; only status 1 continues
    0B52E  rax = qword [rbx + 0xA0]      ; the pointer that is returned
    0B535  ret

So it returns object[+0xA0] when object[+0x4C] is 1, and null otherwise. The argument's TYPE is not recoverable -- the
export has a label but no typed signature that a reader can trust -- so the fields go into a new carrier whose name says
exactly that, following UnknownFlagCarrier rather than pretending they belong to PartObject.

Every edit below is asserted, because a silent no-op is how earlier rounds produced a green check that meant nothing.
"""
import io
import os

ROOT = r"D:\Nesting\nestfab"
IMPL_H = os.path.join(ROOT, "lcns", "include", "lcns", "exports_impl.hpp")
IMPL_C = os.path.join(ROOT, "lcns", "src", "exports_impl.cpp")
LAYOUT = os.path.join(ROOT, "lcns", "include", "lcns", "dll_layout.hpp")
MAP = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")
TEST = os.path.join(ROOT, "lcns", "tests", "test_exports.cpp")


def patch(path, old, new, what):
    t = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    assert old in t, "anchor missing in %s: %s" % (path, what)
    t = t.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8", newline="\n").write(t)
    print("patched %-58s (%s)" % (os.path.basename(path), what))


# 1. the carrier, in the layout header, with the offsets asserted
patch(LAYOUT, "}  // namespace dll",
      '''/**
 * The object behind GetPartWithBadGeometry (ordinal 29, rva 0xB510).
 *
 * Kept separate on purpose: the export has a log label but no typed signature a reader can trust, so only the two offsets
 * its code touches are known. Claiming they are fields of PartObject would be a guess.
 */
struct BadGeometryCarrier {
    unsigned char opaque00[0x4C];
    std::uint32_t status;      // +0x4C, RE 0xB524: only the value 1 continues
    unsigned char opaque50[0x50];
    void* geometry;            // +0xA0, RE 0xB52E: returned when the status is 1
};
static_assert(offsetof(BadGeometryCarrier, status) == 0x4C, "RE 0xB524");
static_assert(offsetof(BadGeometryCarrier, geometry) == 0xA0, "RE 0xB52E");

}  // namespace dll''', "BadGeometryCarrier")

# 2. the declaration
patch(IMPL_H, "void setShearMode(void* order, int value);",
      '''/** RE 0xB510 (ordinals 29/30): returns object[+0xA0] when object[+0x4C] is 1, else null. */
void* getPartWithBadGeometry(void* object);

void setShearMode(void* order, int value);''', "declaration")

# 3. the body
patch(IMPL_C, "void setShearMode(void* order, int value)",
      '''void* getPartWithBadGeometry(void* object) {
    auto* carrier = static_cast<BadGeometryCarrier*>(object);
    if (carrier->status != 1u) {
        return nullptr;
    }
    return carrier->geometry;
}

void setShearMode(void* order, int value)''', "body")

# 4. the forwarding map, keyed by ordinal
patch(MAP, "    {33, reinterpret_cast<void*>(&lcns::dll::exports::impl::getSolutionIdentity)},  // GetSolution",
      '''    {33, reinterpret_cast<void*>(&lcns::dll::exports::impl::getSolutionIdentity)},  // GetSolution
    {29, reinterpret_cast<void*>(&lcns::dll::exports::impl::getPartWithBadGeometry)},  // GetPartWithBadGeometry''',
      "forwarding row")

# 5. the test: a behavioural block, and the two counters it invalidates
patch(TEST, '    return check::finish("exports");',
      '''    // ------------------------------------- GetPartWithBadGeometry (ordinal 29), from its own thirteen instructions
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

    return check::finish("exports");''', "behavioural block")

patch(TEST, "CHECK(ex::forwardedCount() == 14u);", "CHECK(ex::forwardedCount() == 15u);", "count 14 -> 15")
patch(TEST, "                                  e->ordinal0 == 304 || e->ordinal0 == 76;",
      "                                  e->ordinal0 == 304 || e->ordinal0 == 76 || e->ordinal0 == 29;",
      "expected ordinals")

print("")
print("ordinal 29 lands as the fifteenth forwarding entry; the test now expects 15")
