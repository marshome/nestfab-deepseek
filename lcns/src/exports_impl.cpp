// lcns/src/exports_impl.cpp -- the recovered bodies, written against the model in lcns/dll_layout.hpp.
//
// No offset appears here: fields are named, and the layout header asserts each sits where the assembly read it. What stays
// explicit is the one behavioural detail the model must not hide -- that a container's size is computed as RawVector::size
// computes it (byte difference times the derived inverse), not as a division.

#include "lcns/exports_impl.hpp"

namespace lcns {
namespace dll {
namespace exports {
namespace impl {

std::size_t getNumberOfNestings(void* order) {
    return static_cast<NestingOwner*>(order)->nestings.size();
}

std::size_t getNumberOfNestedParts(void* order) {
    return static_cast<NestingOwner*>(order)->sub->parts.size();
}

std::uint32_t getMultiplicity(void* part) {
    return static_cast<PartObject*>(part)->sub->multiplicity;
}

const char* getPartUserString(void* part) {
    return static_cast<PartObject*>(part)->userString;
}

const char* getUserStringAt1B8(void* part) {
    return static_cast<PartObject*>(part)->userString;
}

void setByteAtF8(void* object, int value) {
    static_cast<UnknownFlagCarrier*>(object)->flagF8 = (value != 0) ? 1u : 0u;
}

void setDoubleAndFlag(void* object, int flag, double value) {
    auto* carrier = static_cast<UnknownFlagCarrier*>(object);
    carrier->value100 = value;
    carrier->flagF9 = (flag != 0) ? 1u : 0u;
}

void* getSolutionIdentity(void* handle) {
    return handle;
}

void setShearMode(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field44 = value; }
void setNoMixPreference(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field18 = value; }
void setNoSheetMixPreference(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field1C = value; }
void setShearRepulseFromBorders(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field58 = value; }
void unlockLaunchingOrder(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field244 = value; }
void setInt_1FC(void* order, int value) { static_cast<IntFieldCarrier*>(order)->field1FC = value; }

}  // namespace impl
}  // namespace exports
}  // namespace dll
}  // namespace lcns
