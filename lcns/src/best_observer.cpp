// lcns/src/best_observer.cpp -- Engine::BestObserver, from the three slots that are its whole interface.
//
// THE CLASS FORWARDS. THREE OF ITS SLOTS, 11, 11 AND 18 BYTES, ARE THE SAME TWO INSTRUCTIONS:
//
//     0x755A40  mov rcx, [rcx + 0x10]     ; slot 2: take the object at +0x10
//     0x755A44  mov rax, [rcx]            ; its vtable
//     0x755A47  jmp qword ptr [rax + 0x10] ; and its slot 2
//
//     0x755A50  mov rcx, [rcx + 0x10]     ; slot 3: the same object
//     0x755A57  jmp qword ptr [rax + 0x18] ; its slot 3
//
//     0x755A60  mov rcx, [rcx + 0x10]     ; slot 5: the same object
//     0x755A67  movzx r8d, r8b            ;   with a bool argument narrowed
//     0x755A6F  jmp rax                    ; its slot 5, at [rax + 0x28]
//
// **SO `BestObserver` HOLDS A POINTER AT +0x10 AND DELEGATES ITS INTERFACE TO IT.** The object it points at is an interface whose vtable has
// NULL in slots 0 and 1 -- a pure interface -- and the class's own job is to present it.
//
// AND THAT IS ALL THE INSTRUCTIONS ESTABLISH. The declaration it replaces held
//
//     Solution best_;  double bestScore_ = 0.0;  bool has_ = false;  int offers_ = 0;
//
// **NONE OF WHICH ANY INSTRUCTION PLACES**: the two functions that could construct it (0x756B20 and 0x756CF0) are the destructor pair and
// write only the vtable, and the class's constructor is not in the profile at all. **A member nothing places is not a member**, and four of
// them were sitting in the tree looking recovered.

#include "lcns/nester.hpp"

namespace lcns {

// RE 0x755A40, vtable slot 2: the best solution is offered to the object at +0x10.
void BestObserver::offer(const Solution& solution, double score) {
    if (sink_ != nullptr) {
        sink_->offer(solution, score);
    }
}

// RE 0x755A50, vtable slot 3.
bool BestObserver::hasSolution() const {
    return sink_ != nullptr && sink_->hasSolution();
}

// RE 0x755A60, vtable slot 5. The argument is narrowed with `movzx r8d, r8b` at 0x755A67, so it is a bool.
void BestObserver::notify(bool finished, int offers) {
    if (sink_ != nullptr) {
        sink_->notify(finished, offers);
    }
}

// The three forwarders above are the class's interface; slot 4 at 0x755A80 (4242 bytes) and the destructor pair are separate functions and
// have not been read, so nothing is claimed about them here.

}  // namespace lcns
