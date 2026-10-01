// lcns/canceller.hpp -- the cancellation interface the binary really has.
//
// RE (goal round 88-89): six classes in the image are cancellers, each with a 3 slot vtable:
//     Multi::CompactCanceller      vtable 0xA3B870
//     Multi::NoFitMapCanceller     vtable 0xA3B8E0
//     Multi::RCompactCanceller     vtable 0xA3B910
//     Multi::SupervisorCanceller   vtable 0xA3BA90
//     Utils::Canceller             vtable 0xA3BD70
//     Tiling::WarpCanceller        vtable 0xA3D160
// In the Itanium ABI the first two slots are the complete-object and deleting destructors, so a THREE
// slot table means each class declares exactly one virtual of its own -- the cancellation hook.
//
// RECOVERED: the class names, the table addresses, the three-slot shape, and that the third slot is a
// virtual call target. INFERRED: that the third slot is "cancel" (the names say so, the instructions
// were not read far enough to prove it) and the argument list of that hook, which is modelled here as
// taking no arguments.
#pragma once

#include <atomic>

namespace lcns {

// RE the 3 slot shape of all six cancellers.
class Canceller {
public:
    virtual ~Canceller() = default;      // slot 0 (and slot 1, the deleting destructor)
    virtual void cancel() = 0;           // slot 2, the one virtual each class declares
};

// RE Utils::Canceller as the code uses it: a flag that a long computation polls. The binary stores the
// table address point (vtable + 0x10) into the object, which is what round 87 detected in code.
class FlagCanceller : public Canceller {
public:
    void cancel() override { cancelled_.store(true); }
    bool cancelled() const { return cancelled_.load(); }

private:
    std::atomic<bool> cancelled_{false};
};

}  // namespace lcns
