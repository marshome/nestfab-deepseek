// lcns/docs/WHAT_IS_NORMAL_CPP.md -- the standard this project's C++ has to meet, stated as a comparison rather than as a rule.
//
// The human asked whether I understand what NORMAL C++ looks like, "not stuffed full of offset addresses everywhere". The honest answer has
// two halves: I can state the standard, and the repository already contains code that meets it, so the standard is not a matter of taste.
//
// ================================================================================================================================
// THE COMPARISON. Both of these are from this repository, both carry the module's offsets, and only one is C++.
//
// GOOD -- lcns/model.hpp's Order:
//
//     struct Order {
//         Objective objective = Objective::MinimizeArea;     // +0x08
//         NestingOrigin origin = NestingOrigin::BottomLeft;  // +0x0C
//         double usedSurfaceMinOffcutDimension = 0.0;
//         bool shear = false;                    // +0x44
//         double shearGap = 0.0;                 // +0x50
//         int commonCutAuthorizations[3] = {0, 0, 0};
//         int commonCutModeTag = 0;              // +0x88: 1 = preset (use +0x8C), 0 = objective (+0x90)
//     };
//
// FAKE -- what I generated into class_definitions.hpp:
//
//     void*          at_0010      = {}; // +0x10, RE 0x266E55: mov qword ptr [rbp + 0x10], 0
//     void*          at_0018      = {}; // +0x18, RE 0x266E5D: mov qword ptr [rbp + 0x18], 0
//
// **BOTH CARRY OFFSETS. THE DIFFERENCE IS NOT THE OFFSETS.**
//
// ================================================================================================================================
// THE FIVE DIFFERENCES, and each is checkable.
//
// 1. A NAME THAT MEANS SOMETHING. `usedSurfaceMinOffcutArea` is a quantity. `at_0010` is a position wearing a name. **A name is what makes
//    code readable, and a name needs an oracle** -- the module's own string, an option key, a setter, a log format. Where no oracle exists the
//    honest move is to record the field in a TABLE and leave the class alone until one turns up, NOT to generate a name-shaped position.
//
// 2. A TYPE CHOSEN FOR THE MEANING. `Objective` and `NestingOrigin` are enums whose values were proven. `bool`, `double` and
//    `int commonCutAuthorizations[3]` are the module's own widths AND its own semantics: three authorizations, not 24 bytes.
//    My `void* at_0010` says "eight bytes here" and nothing else -- **a pointer type on something that may be an integer is worse than no
//    type, because it is a claim.** Where the width is all that is known, say so with a byte array rather than inventing a pointer.
//
// 3. THE OFFSET IS A FOOTNOTE. In Order the offsets appear where a reader wants them, several members share one comment, and the comment
//    often adds MEANING (`+0x88: 1 = preset (use +0x8C)`). In mine every line begins with an offset, so the offsets are the content and the
//    code is the annotation. **That is the inversion the human is objecting to.**
//
// 4. GROUPING BY MEANING. Order's members are grouped by subsystem -- objective, offcut, shear, common cut, multi torch -- with a heading per
//    group. Mine are grouped by ADDRESS, ascending, which is the order a disassembler produces and not an order a reader wants.
//
// 5. BEHAVIOUR WHERE THERE IS BEHAVIOUR. Order has methods; NestingNester has run(), estimate() and name(). A class with fields and no
//    methods is fine when the module's class has none, and a class whose methods exist should say so.
//
// ================================================================================================================================
// WHAT THIS MEANS FOR THE GENERATORS, and it is a real change rather than a note.
//
// **A FIELD WITH NO ORACLE DOES NOT BELONG IN A CLASS.** It belongs in the table it is already in, and the class waits. So the generators
// should emit a class member ONLY when they have a name for it, and otherwise leave the class undeclared -- which is the opposite of what I
// built, where a placed offset became a member named after its own address.
//
// The repositories' own evidence decides which names exist: re/param_names.json, re/option_keys.json and re/param_fields2.json hold the option
// names the module answers to, and the offset each lookup result is STORED into. **A name from an option key beside an offset from the same
// instruction is an oracle**, and that pairing -- not the raw store -- is what a legitimate generated class would use.
//
// ================================================================================================================================
// THE TEST FOR A GENERATED HEADER, in one sentence: **could a C++ programmer who has never seen the binary read the class and know what the
// program does?** If the answer is no, the file is a disassembly with a .hpp extension, whatever it is named.
