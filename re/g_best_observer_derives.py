# -*- coding: utf-8 -*-
"""Make Engine::BestObserver derive from Structure_Observer, which is the module's own `Structure::Observer`.

**THE DERIVATION IS IN THE MODULE'S TYPEINFO, NOT INFERRED**: the chain is `N6Engine12BestObserverE -> N9Structure8ObserverE`. The class was declared
standalone, so the relationship existed in the module and nowhere in this tree.

**AND IT IS DECLARABLE NOW BECAUSE THE BASE'S SURFACE IS KNOWN**: six virtuals, of which slots 2, 3 and 5 are the three `BestObserver` forwards and
slot 4 is one it does not.
"""
import io
import sys

NESTER = r"D:\Nesting\nestfab\lcns\include\lcns\nester.hpp"

OLD = """class BestObserver {
public:
    void offer(const Solution& s, double score);      // RE 0x755A40
    bool hasSolution() const;                          // RE 0x755A50
    void notify(bool finished, int offers);            // RE 0x755A60

private:
    Structure_Observer* sink_ = nullptr;                     // +0x10, RE 0x755A40: mov rcx, [rcx + 0x10]
};"""

NEW = """class BestObserver : public Structure_Observer {   // RE the typeinfo chain: N6Engine12BestObserverE -> N9Structure8ObserverE
public:
    // slot 2, slot 3 and slot 5, each forwarding to the object at +0x10
    void offer(const Solution& s, double score) override;      // RE 0x755A40
    bool hasSolution() const override;                          // RE 0x755A50
    void notify(bool finished, int offers) override;            // RE 0x755A60

    /** **SLOT 4 IS NOT FORWARDED BY THIS CLASS** -- the module's own table has it, and RE 0x755A80 is the 4242 byte routine at that slot. Its body
     *  has not been read, so this says so rather than inventing one. */
    void slot4() override {}

private:
    Structure_Observer* sink_ = nullptr;             // +0x10, RE 0x755A40: mov rcx, [rcx + 0x10]
};"""


def main():
    text = io.open(NESTER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD not in text:
        print("REFUSING: the BestObserver declaration is not as expected")
        return 2
    text = text.replace(OLD, NEW, 1)
    io.open(NESTER, "w", encoding="utf-8", newline="\n").write(text)
    print("BestObserver now derives from Structure_Observer and overrides three of its four virtuals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
