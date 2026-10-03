// lcns/src/observers.cpp -- Engine::EquivalentObserver and Engine::CompositeObserver, the other two
// `Structure::Observer` implementations the module's own typeinfo names.
//
// **THE THREE DERIVATIVES SPLIT TWO WAYS, AND THAT IS WHAT THESE TWO CLASSES ARE FOR.** `BestObserver`
// (lcns/src/best_observer.cpp) forwards slots 2, 3 and 5 to an object at **+0x10**. These two were read
// from their slot bodies in `re/vtables.json` and the slots are not the same shape:
//
//   Engine::EquivalentObserver   vtable 0xA3D0A0, N6Engine18EquivalentObserverE
//     slot 2  0x75DDD0   11 B   mov rcx, qword ptr [rcx + 8] / mov rax, [rcx] / jmp [rax + 0x10]
//     slot 3  0x75DDE0   11 B   the same shape
//     slot 5  0x75DDF0  621 B   its own body
//
//   Engine::CompositeObserver    vtable 0xA3D060, N6Engine17CompositeObserverE
//     slot 2  0x75CBC0  193 B   **ITS OWN BODY** -- not an 11-byte forward
//     slot 3  0x75CC90  152 B   **ITS OWN**
//     slot 5  0x75CD30  100 B   its own
//
// **SO `EquivalentObserver`'s FIELD IS AT +0x08 AND `BestObserver`'s IS AT +0x10**, which is why they are
// two declarations: a shared base holding the pointer at one offset would make one of them wrong, and the
// instructions say two different offsets.
//
// **AND `CompositeObserver` FORWARDS NOTHING**, which is what the note above `Structure_Observer` in
// lcns/include/lcns/nester.hpp was measuring when it found slot 2 to be `xor eax, eax; ret` in TWO of the
// three -- the two forwarders. **The third answers for itself, so it declares NO member**: a slot body
// being present is not evidence about an object's fields, and inventing a `sink_` for it would be exactly
// the shape-matching this project forbids.

#include "lcns/nester.hpp"

namespace lcns {

EquivalentObserver::EquivalentObserver() = default;

// RE 0x75DDD0, vtable slot 2: the object at +0x08 receives the offer.
void EquivalentObserver::offer(const Solution& solution, double score) {
    if (sink_ != nullptr) {
        sink_->offer(solution, score);
    }
}

// RE 0x75DDE0, vtable slot 3: the same eleven-byte shape, so it forwards the question.
bool EquivalentObserver::hasSolution() const {
    return sink_ != nullptr && sink_->hasSolution();
}

// RE 0x75DDF0, vtable slot 5. 621 bytes and its own body -- it does NOT forward, so there is no sink_ read
// in it. What it does with the two arguments has not been read, so nothing is claimed about the outcome.
void EquivalentObserver::notify(bool finished, int offers) {
    (void)finished;
    (void)offers;
}

CompositeObserver::CompositeObserver() = default;

// RE 0x75CBC0, vtable slot 2, 193 bytes: an own body, not a forward. The body has not been read, so the
// class declares no member to delegate to and this records the observation rather than a behaviour.
void CompositeObserver::offer(const Solution& solution, double score) {
    (void)solution;
    (void)score;
}

// RE 0x75CC90, vtable slot 3, 152 bytes, its own.
bool CompositeObserver::hasSolution() const {
    return false;
}

// RE 0x75CD30, vtable slot 5, 100 bytes, its own.
void CompositeObserver::notify(bool finished, int offers) {
    (void)finished;
    (void)offers;
}

}  // namespace lcns
