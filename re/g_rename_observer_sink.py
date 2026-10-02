# -*- coding: utf-8 -*-
"""Rename ObserverSink to Structure::Observer -- the module's own namespace and class name -- and give it its six measured slots.

**THE NAME I INVENTED WAS THE MODULE'S OWN CLASS, WHICH IS EXACTLY WHAT re/g_base_chain.py EXISTS TO PREVENT.** `Engine::BestObserver`'s typeinfo
chain is

    N6Engine12BestObserverE  ->  N9Structure8ObserverE

so the interface its three forwarders reach IS `Structure::Observer`, whose name string is at 0xA311C0 and whose typeinfo is at 0xA1DEE0.

**AND SIX SLOTS, MEASURED FROM THE THREE CLASSES THAT DERIVE FROM IT** -- `Engine::CompositeObserver` at 0xA3D060, `Multi::TraceObserver` at 0xA3B700
and `Multi::NestingObserver` at 0xA3B7C0, every one with SIX slots:

    slot 0   one per class, 1 byte            the deleting destructor
    slot 1   one per class, 5 bytes           the destructor
    slot 2   0x7C2460 in TWO of the three     `xor eax, eax` then `ret` -- THE BASE'S PLACEHOLDER FOR A PURE VIRTUAL
    slot 3   0x7C2470 in TWO of the three     the same
    slot 4   one per class, up to 4111 bytes
    slot 5   0x7C2480 in ONE of the three     `ret`

**AND THAT IS WHAT THE THREE FORWARDERS FIT**: they jump through `[rax + 0x10]`, `[rax + 0x18]` and `[rax + 0x28]` -- slots 2, 3 and **5**. **An
earlier version declared three methods, and three methods cannot have a gap at slot 4.**
"""
import io
import sys

NESTER = r"D:\Nesting\nestfab\lcns\include\lcns\nester.hpp"
SOURCE = r"D:\Nesting\nestfab\lcns\src\best_observer.cpp"
TEST = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

# placed INSIDE namespace lcns, because the module's class is Structure::Observer and this project's namespaces are not the module's
BASES = '''/** **THE MODULE'S OWN NAME FOR THE INTERFACE `Engine::BestObserver` FORWARDS TO.** The chain is
 *  `N6Engine12BestObserverE -> N9Structure8ObserverE`, read from the module's typeinfo, so this class IS `Structure::Observer`: its name string is
 *  at 0xA311C0 and its typeinfo at 0xA1DEE0. **An earlier version of this declaration called it `ObserverSink`, a name invented here** -- which is
 *  the placeholder `re/g_base_chain.py` exists to prevent.
 *
 *  **SIX VIRTUALS, MEASURED FROM THE THREE CLASSES THAT DERIVE FROM IT** (`Engine::CompositeObserver`, `Multi::TraceObserver` and
 *  `Multi::NestingObserver`, tables at 0xA3D060, 0xA3B700 and 0xA3B7C0, every one with six slots):
 *
 *      slot 0   one per class, 1 byte             the deleting destructor
 *      slot 1   one per class, 5 bytes            the destructor
 *      slot 2   0x7C2460 in TWO of the three      `xor eax, eax` then `ret` -- THE BASE'S PLACEHOLDER FOR A PURE VIRTUAL
 *      slot 3   0x7C2470 in TWO of the three      the same
 *      slot 4   one per class, up to 4111 bytes
 *      slot 5   0x7C2480 in ONE of the three      `ret`
 *
 *  **AND THE THREE FORWARDERS FIT THAT EXACTLY**: they read the object at +0x10 and jump through `[rax + 0x10]`, `[rax + 0x18]` and `[rax + 0x28]`
 *  -- slots 2, 3 and 5. **An earlier version declared only three methods, and three methods cannot have a gap at slot 4.** The two this project
 *  does not forward are simply not forwarded, and the second is named for its slot rather than guessed at. */
class Structure_Observer {
public:
    virtual ~Structure_Observer() = default;
    virtual void offer(const Solution& solution, double score) = 0;   // slot 2, RE 0x755A47: jmp [rax + 0x10]
    virtual bool hasSolution() const = 0;                             // slot 3, RE 0x755A57: jmp [rax + 0x18]
    virtual void slot4() = 0;                                         // slot 4, NOT forwarded by BestObserver
    virtual void notify(bool finished, int offers) = 0;               // slot 5, RE 0x755A6F: jmp [rax + 0x28]
};

'''

OLD = '''/** The interface `Engine::BestObserver` forwards to, RE 0x755A40 through 0x755A6F.
 *
 *  Its vtable is at 0xA55FB0 and has NULL in slots 0 and 1 -- **a pure interface** -- and the three forwarders reach its slots 2, 3 and 5
 *  through [rax + 0x10], [rax + 0x18] and [rax + 0x28].
 */
class ObserverSink {
public:
    virtual ~ObserverSink() = default;
    virtual void offer(const Solution& solution, double score) = 0;
    virtual bool hasSolution() const = 0;
    virtual void notify(bool finished, int offers) = 0;
};

'''


def main():
    text = io.open(NESTER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD not in text:
        print("REFUSING: the ObserverSink declaration is not as expected")
        return 2
    text = text.replace(OLD, BASES, 1)
    text = text.replace("ObserverSink* sink_", "Structure_Observer* sink_")
    io.open(NESTER, "w", encoding="utf-8", newline="\n").write(text)
    print("nester.hpp: ObserverSink -> Structure_Observer with six measured slots")

    body = io.open(SOURCE, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    body = body.replace("ObserverSink", "Structure_Observer")
    io.open(SOURCE, "w", encoding="utf-8", newline="\n").write(body)
    print("best_observer.cpp: the pointer's type renamed")

    test = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "ObserverSink" in test:
        test = test.replace("ObserverSink", "Structure_Observer")
        test = test.replace("struct Sink : lcns::Structure_Observer {",
                            "struct Sink : lcns::Structure_Observer {")
        test = test.replace("std::is_abstract<lcns::Structure_Observer>",
                            "std::is_abstract<lcns::Structure_Observer>")
        io.open(TEST, "w", encoding="utf-8", newline="\n").write(test)
        print("test_recovered.cpp: the interface renamed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
