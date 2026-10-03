// lcns/include/lcns/engine_base.hpp -- `Engine::Engine`, the base of the whole engine family.
//
// **IT LIVES IN ITS OWN HEADER BECAUSE TWO HEADERS NEED IT AND ONE INCLUDES THE OTHER.** `engines.hpp` carries the six concrete engines and includes
// `engines_composite.hpp`; that header's `CompositeEngine` could not name this base without a cycle, **so it was declared with NO base class and its `run` without `override`
// while the module's own vtable says it is an engine like the rest** -- `re/vtables.json` has `N6Engine15CompositeEngineE` at 0xA3D000 with the same three slots.
//
// **THE CLASS IS `Engine::Engine` AND NOT `EngineBase`**: the mangled names in `re/vtables.json` are `N6Engine...` for all seven concrete classes, and there is no entry
// ending in `6EngineE` because an abstract base has no instantiated table -- **which is also why the whole base layer was missing from this tree.** The name here is the
// port's; the module's is the namespace and class the mangled prefix spells.
//
// **THE BASE'S SIZE IS 0x10 AND FOUR INDEPENDENT CONSTRUCTORS SAY SO**: each zeroes a BYTE at +0x08 and a DWORD at +0x0C **before** installing its vtable, which is what
// constructing a base sub-object looks like, and each then places its first own member at +0x10. **The eleven members an earlier version declared from +0x00 to +0x50 were
// eight bytes low, every one of them** -- see the note on the members below for what that declaration had actually captured.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

class EngineBase {
public:
    virtual ~EngineBase() = default;

    /** Slot 2, RE 0x2516E. The default is pure, so a subclass must say what it does rather than inherit silence. */
    virtual void* run(const void* problem, double timeLimit, void* observer, void* result) = 0;

protected:
    /** **THE BASE IS A VPTR, A BYTE AND A DWORD -- AND THE ELEVEN MEMBERS THAT STOOD IN `engines.hpp` WERE NOT THE BASE'S AT ALL.**
     *
     * **WHAT SETTLED IT WAS A CONSTRUCTOR PREAMBLE, WHICH IS THE EVIDENCE NINE ROUNDS OF READING `run` BODIES COULD NOT GIVE.** FOUR independent engine constructors zero
     * these two offsets **BEFORE** installing their vtable, which is what constructing a base sub-object looks like:
     *
     *      0x24AB0  EquivalentEngine   024ACA byte [rax+8],0   024ACE dword [rax+0xc],0   024ADC vtable   024AE2 first own member at +0x10
     *      0x240D0  MultiEngine        024100 byte [rax+8],0   024104 dword [rax+0xc],0   02411A vtable   024116 dword [rbx+0x10]
     *      0x24B80  DelayedEngine      024BA6 byte [rax+8],0   024BAA dword [rax+0xc],0   024BB1 vtable   024BBE qword [rbx+0x10]
     *      0x24FD0  InfiniteEngine     024FFC byte [rax+8],0   025006 dword [rax+0xc],0   02500D vtable   02501A qword [rbx+0x10]
     *
     * **AND `0x23E70` (`NestingEngine`) WRITES THE SAME TWO OFFSETS WITH THE VALUE 1** -- `023F93` and `023F9A` -- **which is why they are flags or counters and not a
     * pointer.**
     *
     * **SO THE BASE ENDS AT 0x10 AND THE DERIVED CLASSES START THERE.** What the deleted declaration had captured was **an agreement between FOUR SIBLINGS about their own
     * shared layout** -- and **an agreement between siblings is not an inherited member.** **What the two fields MEAN is not established**; a sweep of every function in the
     * image that touches them found five adjacent functions whose `+0x0C` turned out to be a `shared_ptr` control block's WEAK count, **so adjacency proved nothing.** */
    std::uint8_t at08 = 0;         // +0x08, RE 0x024ACA `mov byte ptr [rax + 8], 0` and 0x023F93 `dword ptr [rax + 8], 1`
    std::uint32_t at0C = 0;        // +0x0C, RE 0x024ACE `mov dword ptr [rax + 0xc], 0` and 0x023F9A `dword ptr [rax + 0xc], 1`
};

/** What RE 0x759AB0 reads out of the SECOND argument: the engine it delegates to sits at +0x10 of the problem. */
struct ProblemView {
    std::byte header[0x10]{};
    EngineBase* engine = nullptr;      // RE 0x759AB0: mov rdx, [rdx + 0x10]
};

}  // namespace lcns
