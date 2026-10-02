# The C++ tree, audited -- what holds code, what holds data, and what holds claims nothing supports

The human asked for a full check of the C++ code, after finding four separate instances of the same defect by hand. This is the result, and it
splits into **what a tool can decide** and **what only reading can**, because conflating those is how the defect survived four rounds.

## 1. SHAPE -- decided mechanically, and now zero

re/g_full_cpp_audit.py over **115 files**:

    CODE          97
    DATA          18     registries whose subject genuinely IS a list, each with a stated reason
    OFFSET-HEAVY   0
    EMPTY          0
    FABRICATED     0

It looks for four shapes, each of which the human found in this repository: a member named after its own offset (`at_0020`), a **member whose
comment cites a stack store** (`mov [rsp + 0x20], rax` -- the stack is not the object), an `unplaced_XXXX` byte region standing in for a type, and
a placeholder class. **All four are gone.**

**AND THE CHECK WAS WRONG TWICE BEFORE IT WAS RIGHT**, which is why it ships with a proof:

  * the first version flagged any line mentioning `mov [rsp + ...]`, and reported **four correct files** -- `geom.hpp`, `variant.hpp`,
    `licensing.cpp` -- where the stack store appears in a COMMENT citing evidence, which is legitimate. The fabricated form is narrower: a
    MEMBER DECLARATION whose comment cites one.
  * re/g_prove_full_audit.py plants each of the four shapes in turn and requires the audit to fail and name the file:

        planted a member named after its offset                -> exit 1, named
        planted a member whose comment cites a stack store     -> exit 1, named
        planted an unplaced byte region standing in for a type -> exit 1, named
        planted a placeholder class                            -> exit 1, named

## 2. SUPPORT -- needing reading, and NOT clean

re/g_members_without_instructions.py asks the question the shape audit cannot: **does the class's recovered constructor actually WRITE the members
the class declares?** Of 19 hand-written classes it can check:

**SEVEN DECLARE MEMBERS THAT NO INSTRUCTION IN THEIR CONSTRUCTOR PLACES:**

    class                header             ctor       writes      declared members
    Supervisor           engine.hpp         0x30B60    none        order_, ctx_, params_, strategies_, mu_
    InfiniteEngine       engines.hpp        0x24FD0    none        inner_
    BestObserver         nester.hpp         0x756B20   none        best_, bestScore_, has_, offers_
    Squeezer             row.hpp            0x138A20   none        enabled_, coeff_, threshold_, twiceMaxExtent
    PackerCache          tiling.hpp         0x158BE0   none        keys_, entries_
    MultiOrientedPattern tiling.hpp         0x4F2910   none        angle, flipped, partIndex_, orientations_
    MultitorchEvaluator  tiling.hpp         0x4E8410   none        nbTorches_
    BoxMultiTiler        tiling.hpp         0x4F4850   none        evaluators_

**AND SEVERAL MORE WHERE THE WRITES AND THE DECLARATION DISAGREE:**

    LimitedNester    declares maxParts_, maxAngles_   but the constructor writes +0x20 +0x28 +0x38 +0x40
    RowNester        declares pipe_, cfg18_, cfg20_, core_   but the constructor writes ONLY +0x18
    Canceller        declares cancelled_              but the constructor writes +0x37A +0x3C0 +0x3C8 +0x3D0
    BestNester       declares children_               but the write is +0x10, not a vector's +0x08

**AND TWO THAT AGREE, which is what the rest should look like:**

    FlipNester     record_ and compare_ at +0x20 and +0x21      RE 0x4B59B and 0x4B5AE write both
    FilterNester   inner_, seed_, rng_ at +0x18, +0x10, +0x20   RE 0xB4449, 0xB4455, 0xB3AB0 write all three

## 3. WHAT THIS MEANS, WITHOUT SOFTENING IT

**The shape is clean and the support is not.** Every member in the tree is written the way C++ is written -- names, types, constructors,
methods, no `at_0020`, no `kVtable` in a class -- **and a substantial minority of those members are not placed by anything that was read.** They
came from the same weakness that produced `FlipNester`'s invented `ratio_`: a plausible member at a plausible offset, written when the class was
declared and never checked against the constructor afterwards.

**A class declaration is a claim, and the claim has to be re-read against the instructions, one class at a time.** That is the work the next
rounds are, and the list above is the queue. Two classes have been through it; seventeen have not.
