# LaunchLocalComputation -- the terrain, and the order to take it

## The export

| field | value |
|---|---|
| rva | **0x2AB0** |
| ordinals | 51 (primary), 52 |
| size | **2134 bytes, 491 instructions** |
| signature (inferred) | `void LaunchLocalComputation(LaunchingOrder* order, double something)` -- rcx is the order and xmm1 a double, since the head does `rbp = rcx` and `r13 = xmm1` |

Two other exports are thin wrappers over it, so this one entry point carries three ordinals:

* `0x3310` ordinal 164 `LaunchLimitedLocalComputation`: saves `[order+0x1F8]`, sets it to 1, loads a double constant from rip, calls 0x2AB0, then restores the field. 66 bytes. It logs 'LaunchLimitedLocalComputation' through 0x64AEA0 first.
* `0x3360` ordinal 216 `LaunchEstimateLocalComputation`: sets `[order+0x288]` to 1 and tail calls 0x2AB0 with the same double. 52 bytes. It logs '// LaunchEstimateLocalComputation' first.

## Progress: the closure is seven functions and 6636 bytes, with no library code left in it

The closure was **1208 domain functions and 713168 bytes**. The label pass took it to 136, batch seven read and classified
all 38 leaves (to 131), batches eight and nine read the depth one layer whole and classified it (to 26), and batches ten to
thirteen implemented the constructor, the node layout, the module switch and the engine fetch and classified the rest (to
**seven functions and 6636 bytes**). The readings are `re/LEAVES51.txt` for the leaves and the round 525 to 532 sections of
`re/CATEGORIES.md`; `re/EXPORT_BODIES.md` carries the bodies.

What remains, with what is known about each. After batch fourteen the closure is **seven functions and 6636
bytes** with no library code left in it, which is the number this objective is actually working against:

| rva | bytes | what it is |
|---|---:|---|
| `0x2AB0` | 2134 | the orchestration itself; the head and the tail are below |
| `0x3310`, `0x3360` | 118 | the two wrappers, read whole, waiting on 0x2AB0 |
| `0x1BE70` | 109 | the lazy initialiser of the module's own static: a global byte guard, `__cxa_guard_acquire` at 0x998DA0, the construction through 0x65A530, and the object's address returned. Its shape is the one round 427 found in 0xAB20 |
| `0x1BF00` | 18 | calls 0x1BE70 and returns `[[static]+1]`: a byte flag of that static |
| `0x1BF40` | 149 | calls 0x1BE70, tests `[static]`, then two module globals, and returns the address of a third or null: the fast path. Its literal is `c:\Temp\debug_nest.txt` |
| `0x22A20`, `0x22E30` | 1037 + 9 | the constructor 0x2AB0 calls once: `0x2D31` allocates **0x1C8 bytes** through 0x998500 and calls `0x22E30(obj, order, xmm2=the double, r9=1)`. The thunk widens the fourth integer argument before the tail call. The constructor stores the order at +0, builds a container at +0x10 whose begin and end point at its own inline buffer at +0x18, copies eight bytes from `[order+0x220]` through 0x9302C0 into +0x20, sets a two-node list at +0x28 and +0x30, the double at +0x40, the flag at +0x48, the constant 9 at +0x4C, an empty container at +0x50, and three string members at +0xD0, +0xF8 and +0x118. **Its tail (round 529) is where its semantics are**: it reads a mode from `[order+0x240]` and configures a limit flag at +0x150, an iteration cap at +0x154 and two doubles at +0x158 and +0x160 -- 500 with 10.0 and 0.2 in mode 1, 10 with 3.0 in mode 2, and 10 with 4.0 and 0.1 otherwise. The head and the tail are both implemented in `lcns/include/lcns/field_accessors.hpp` and asserted by `lcns/tests/test_boxacc.cpp`, the tail over all four mode values |
| `0x65A530` | 616 | builds three `basic_ofstream`s over `c:\Temp\log_nest.txt`, `c:\Temp\cloud_nest.txt` and `c:\Temp\local_nest.txt` and records whether each of the three is usable at +0, +1 and +2, with +2 forced to 0 when +1 is 0. It is called from 0x1BE70, so it initialises the module's static |
| `0x7BB430` | 495 | stores 0x30, tests `[order+0xE8]`, writes five property strings through 0x978010, calls 0x8693D0 for 0x40 bytes, runs `cpuid` and writes the vendor string, then another block through 0x1B170. Its own literals include `CNS informations` |
| `0x8693D0`, `0x8688E0` | 545 each | called by 0x7BB430 and by 0x2AB0 with a size argument; both build a string-like object |
| `0x5007C0` | 716 | a destructor over the object at `[rcx]`: frees the node list at +0x2A8, the member at +0x280 through 0x531F20, the vector of shared_ptr at +0x268 and the container at +0x70 through 0x92ECB0 |
| `0x8F9220` | 1462 | read in batch twelve: the vector of pointers growth -- begin and end at [rcx] and [rcx+8], the distance over 8, the 0x1FFFFFFFFFFFFFFF bound, the doubled capacity and the eight byte minimum. Classified as library, not domain |
| `0x92B340`, `0x92B940`, `0x92BBA0`, `0x92ECB0` | 2680 | the container releases, read whole in batch fourteen: each recurses up to seven levels into `[node+0x18]`, then frees the node's string and the node. `0x5007C0` calls all four, and each calls itself. Domain, and blocked on the ownership rule the 0x50 byte records imply |
| `0x929FA0` | 1495 | read in batch twelve: recurses six levels into [node+0x18], frees a contiguous array of 0x30 byte slots and the member at +0x28, then the node. Classified as library, not domain |
| `0x9302C0` | 390 | allocates 0x48 bytes and copies 0x28 bytes from `[src+0x20]` into the new node's inline buffer at +0x30: the node copier 0x22A20 calls once. Each node is 0x48 bytes with a back pointer at +0x10, a forward pointer at +0x18, an inline string at +0x20 with its length at +0x28, a type dword at +0 and a double at +0x40 |
| `0x9308C0` | 605 | the release of the same node tree: it recurses on `[node+0x18]`, frees the string when it does not point at +0x30, then frees the node. A list head is passed in the second argument and walked, but the list is built by the constructor and a direct implementation is blocked until the list's owner is known; the node layout and the two free paths are certain |

## What the head and the tail do

    2AB0  save eight registers, reserve 0x208 bytes
    2AC3  rbp = rcx                     ; the launching order
    2AC6  r13 = xmm1                    ; the double, kept for later
    2ACB  call 0x1BF00                  ; if the byte flag is set, jump to 0x31C9, which reads 'cns_force_cloud'
    2AD8  byte [rip + 0xB1C539]         ; a module switch; if zero jump to 0x318A
    2AF8  call 0x63F6C0                 ; the mutex family
    2B05  byte [rsp+0x38] = 1           ; the scope guard
    2B0A  call 0x1BF40                  ; fetch the engine object
    2B1B  call 0x978010 three times     ; the stream writes '-> ', 'LaunchLocalComputation' (0x16 bytes) and a 1 byte value
    2B5A  call 0x8688E0                 ; hand it the double in xmm1
    2B67  [rbx] then [rax-0x18] ...     ; the vtable-relative member access
    2B7F  byte [rsi+0x38] ; 0x867BF0 ; branch into the engine

    2BB6  build the input file stream over 'c:\Temp\cns.pb.json' by hand: 0x945370, 0x9454D0, 0x87EDF0, 0x87D590
    2CA2  call 0x1EE50, 0x5070E0, 0x5007C0
    2D31  allocate 0x1C8 bytes, call 0x22E30 -> the constructor above
    2D54  read [order+0x1D0] and [order+0x1D8]: the end and the capacity of a vector of pointers at +0x1D0
    2D92  if the vector had no room, 0x3144: the storage paths and 'c:\Temp\cns.pb.json'
    314F  '// LaunchLocalComputation'
    318A  the module-switch-off path
    31C9  'cns_force_cloud' and, through 0x9308C0, the server list 'cns1.optalog.com;cns2.optalog.com'
    31E9  the stream-state path
    3236  the vector-append path
    32AC  the null engine path
    32FA  the guard was taken by someone else

## The order to take it

1. **Read 0x22A20 whole and implement it.** It is the object the orchestration is about, its field map is already half read,
   and it is the only construction 0x2AB0 performs. It needs 0x9302C0 and 0x9308C0, which are 390 and 605 bytes.
2. **Then 0x5007C0**, its destructor, which is the same object seen from the other end and needs 0x92B340, 0x92B940,
   0x92BBA0 and 0x92ECB0.
3. **Then 0x7BB430 and 0x8F9220**, then 0x929FA0.
4. **Then write 0x2AB0 itself**, and with it the wrappers 0x3310 and 0x3360, which are already read whole: ordinal 51 and 52,
   164 and 165, 216 and 217 all forward together, which is where `forwardedCount` goes up by six.

## The counting rule, which decides what "done" means here

Reading the closure whole showed that almost all of it is libstdc++: the iostreams, the locale facet caches and their
accessors, the numeric formatting layer, the shared_ptr reference counting. That is not domain behaviour and reimplementing
it would add code without adding recovery. The rule this project already applies to the platform-forwarding class applies
here too: such a function is **classified and recorded, not counted**, with the evidence next to its address in
`re/g_toolchain.py`. `re/g_domain_closure.py` computes what is left under that rule, forward from the entry point, so that
nothing reached only through library code can enter the work list.

## How to see the work list

    python re/g_domain_closure.py 51          # the domain set, in work order, with the leaves marked
    python re/g_closure_work.py 51 12 2000    # the whole closure in work order with leaf bodies
    python re/g_callers.py 0x22A20            # who calls it, inside the closure first
    .\re\gate.ps1                             # the whole gate, which sets its own environment


## Where the reader is, and what is implemented (rounds 534 to 536)

**The object is the launch order, 0x2C0 bytes**, and its layout is C++ now: `lcns/include/lcns/launching_order.hpp`, read out
of `0x14620 NewLaunchingOrder`, which allocates 0x2C0 through operator new and writes 96 fields, the largest at +0x2B8.
`re/g_ctor_fields.py 0x14620` prints them all. This is the type `0x2AB0` receives, the type `0x5007C0` destroys, and the type
`0x2AB0` reads its mode from at +0x240.

**The node is 0x48 bytes and IS implemented**: `lcns/include/lcns/cns_node.hpp` holds `0x9302C0` (the copy) and `0x9308C0`
(the release), with the ownership rule the instructions gave -- a string is owned exactly when its pointer is not the node's
own +0x30. `test_recovered.cpp` runs both halves of that rule, an inline string and an outside string, because a release that
frees an inline buffer is the failure the rule exists to prevent.

**The field names have a stated bar**: two independent single-offset accessors must agree on the offset before a name is
used. Six names exist for this object and two clear the bar (+0x10 and +0x50, and both of those belong to the SOLUTION, whose
layout coincides with the order's at those two offsets); the other four carry their single witness in the header. Everything
else keeps slotXXX with the reason written above it.

**The serialisers are located**: `..\structure\text_io.cpp` holds the JSON vocabulary -- ToJson (0x50DB70) writes valid,
version, number_of_nested_parts, nestings, sheet_id, multiplicity, common_cut_evaluation, multitorch_infos, number_of_groups,
fill_ratio, min_x, min_y; LoadSheet (0x5091B0) reads geometry, quantity, dimension_x, dimension_y, left_gap, right_gap,
bottom_gap, top_gap, defect_gap; LoadCommonCutEvaluation (0x509A40) reads common_cut, left, right, left_index, right_index,
valid, linked, number_of_common_cut, common_cut_length, regarding_length, segments. Pairing a key to its offset needs the
value flow (key -> the accessor -> the JSON constructor argument), not the nearest accessor, and `re/g_json_fields.py` shows
why: several accessor calls follow each key and the wrong pairing is invisible.

What that leaves in the closure: `0x2AB0` (2134), `0x3310` and `0x3360` (118, both read whole), `0x5007C0` (716, the order's
destructor), `0x870070` (1106) and the four container releases `0x92B340`, `0x92B940`, `0x92BBA0`, `0x92ECB0` (2680). The four
releases are one shape -- recurse into the chain at [node+0x18], free the string, free the node, walk the list at [node+0x10]
-- which is the shape already implemented at 0x9308C0, so they are next, and `0x92ECB0` first because 180 functions call it.

The C++ added so far, for the record, because `forwardedCount` has not moved and the reason should be visible: the launch
order layout (189 lines), the node copy and release (167), the candidate constructor and the module switch (141), and 195
lines of tests that hold them to their RE addresses. None of those is an export entry, so the count stays at 31 until 0x2AB0
itself is written -- which needs the containers, which need the four releases.
