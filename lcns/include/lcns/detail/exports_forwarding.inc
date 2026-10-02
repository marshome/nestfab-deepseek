// HAND-WRITTEN, not generated. The forwarding map: which entry points run a recovered implementation.
//
// Keyed by ORDINAL -- the module exports by ordinal (NumberOfNames = 0) and the names this project uses were
// recovered from the labels the functions log, so two entries can share a label.
//
// Every line here is a claim that the named implementation agrees with the assembly at the entry's rva, and each
// one carries a test that says how that was established (a differential test where the original can be executed,
// a behavioural test where it cannot). An entry left out fails loudly and returns the documented neutral value.

const Forwarding kForwarding[] = {
    {25, reinterpret_cast<void*>(&lcns::dll::exports::impl::getNumberOfNestings)},   // GetNumberOfNestings
    {23, reinterpret_cast<void*>(&lcns::dll::exports::impl::getNumberOfNestedParts)},   // GetNumberOfNestedParts
    {17, reinterpret_cast<void*>(&lcns::dll::exports::impl::getMultiplicity)},   // GetMultiplicity
    {27, reinterpret_cast<void*>(&lcns::dll::exports::impl::getPartUserString)},   // GetPartUserString
    {210, reinterpret_cast<void*>(&lcns::dll::exports::impl::getUserStringAt1B8)},  // sub_16CF0 (no label)
    {288, reinterpret_cast<void*>(&lcns::dll::exports::impl::setByteAtF8)},         // sub_AFF0 (no label)
    {286, reinterpret_cast<void*>(&lcns::dll::exports::impl::setDoubleAndFlag)},    // sub_B000 (no label)
    {33, reinterpret_cast<void*>(&lcns::dll::exports::impl::getSolutionIdentity)},  // GetSolution
    {73, reinterpret_cast<void*>(&lcns::dll::exports::impl::setLocalEngine)},
    {82, reinterpret_cast<void*>(&lcns::dll::exports::impl::setLocalMaximumThreads)},
    {316, reinterpret_cast<void*>(&lcns::dll::exports::impl::setEvaluateIntermediateNestingsAsLast)},
    {336, reinterpret_cast<void*>(&lcns::dll::exports::impl::setReorganizeBiggestPartNearOrigin)},
    {338, reinterpret_cast<void*>(&lcns::dll::exports::impl::setReorganizeLongestPartNearOrigin)},
    {334, reinterpret_cast<void*>(&lcns::dll::exports::impl::forcePartInsideHole)},
    {78, reinterpret_cast<void*>(&lcns::dll::exports::impl::setObjective)},
    {212, reinterpret_cast<void*>(&lcns::dll::exports::impl::setShearGap)},
    {238, reinterpret_cast<void*>(&lcns::dll::exports::impl::noFitGetNumberOfExternalPolygons)},
    {144, reinterpret_cast<void*>(&lcns::dll::exports::impl::setFillLastNestingStrategy)},  // SetFillLastNestingStrategy
    {166, reinterpret_cast<void*>(&lcns::dll::exports::impl::setPartCommonCutMode)},  // SetPartCommonCutMode
    {182, reinterpret_cast<void*>(&lcns::dll::exports::impl::setFloatingMode)},  // CNS_SetFloatingMode
    {312, reinterpret_cast<void*>(&lcns::dll::exports::impl::setOriginPackingMode)},  // CNS_SetOriginPackingMode
    {330, reinterpret_cast<void*>(&lcns::dll::exports::impl::setPartialShearMode)},  // SetPartialShearMode
    {29, reinterpret_cast<void*>(&lcns::dll::exports::impl::getPartWithBadGeometry)},  // GetPartWithBadGeometry
    {84, reinterpret_cast<void*>(&lcns::dll::exports::impl::setInt_1FC)},   // SetLocalMaximumIterations, offset 0x1FC
    {146, reinterpret_cast<void*>(&lcns::dll::exports::impl::setShearMode)}, // SetShearMode, offset 0x44
    {188, reinterpret_cast<void*>(&lcns::dll::exports::impl::setNoMixPreference)}, // CNS_SetNoMixPreference, offset 0x18
    {222, reinterpret_cast<void*>(&lcns::dll::exports::impl::setNoSheetMixPreference)}, // CNS_SetNoSheetMixPreference, offset 0x1C
    {304, reinterpret_cast<void*>(&lcns::dll::exports::impl::setShearRepulseFromBorders)}, // SetShearRepulseFromBorders, offset 0x58
    {76, reinterpret_cast<void*>(&lcns::dll::exports::impl::unlockLaunchingOrder)}, // UnLockLaunchingOrder, offset 0x244
};
const std::size_t kForwardingCount = sizeof(kForwarding) / sizeof(kForwarding[0]);
