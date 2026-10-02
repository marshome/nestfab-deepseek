# LaunchLocalComputation -- the terrain, and the order to take it

## The export

| field | value |
|---|---|
| rva | **0x2AB0** |
| ordinals | 51 (primary), 52 |
| size | **2134 bytes, 491 instructions** |
| signature (inferred) | `void LaunchLocalComputation(LaunchingOrder* order, double something)` -- rcx is the order and xmm1 a double, since the head does `rbp = rcx` and `r13 = xmm1` |

Two other exports are thin wrappers over it, so this one entry point carries three ordinals:

* `0x3310` ordinal 164 `LaunchLimitedLocalComputation`: saves `[order+0x1F8]`, sets it to 1, loads a double constant from rip, calls 0x2AB0, then restores the field. 66 bytes.
* `0x3360` ordinal 216 `LaunchEstimateLocalComputation`: sets `[order+0x288]` to 1 and tail calls 0x2AB0 with the same double. 52 bytes.

## The closure: this is the whole engine

`re/g_closure_of.py 51` reports **1208 domain functions, 713168 bytes**. For comparison, the direct closures of all other unimplemented exports together came to about 582 KB with the older, more permissive classifier. There is no larger single closure in this module, and there is no shortcut around it: LaunchLocalComputation is the entry point that drives the local optimiser, so a complete implementation of it is a complete implementation of the engine.

The closure is enumerated leaves-first in the tool output, so it doubles as the work order: the deepest entries have no domain dependencies of their own and can be implemented straight away.

## What the head does, read in two passes (rounds 509 and 510)

    2AB0  save eight registers, reserve 0x208 bytes
    2AC3  rbp = rcx                     ; the launching order
    2AC6  r13 = xmm1                    ; a double argument, kept in a register for later
    2ACB  call 0x1BF00                  ; an early-out predicate; if true jump to 0x31C9
    2AD8  byte [rip + 0xB1C539]         ; a module flag; if zero jump to 0x318A
    2AF8  call 0x63F6C0                 ; the same mutex family the other exports use
    2B05  byte [rsp+0x38] = 1           ; a guard flag for the scope
    2B0A  call 0x1BF40                  ; fetch an engine or scheduler object
    2B1B  call 0x978010 three times     ; set three properties, with lengths 3, 0x16 and 1
    2B5A  call 0x8688E0                 ; hand it the double
    2B67  [rbx] then [rax - 0x18] ...   ; the usual vtable-relative member access
    2B7F  byte [rsi + 0x38] ; 0x867BF0 ; branch into the engine

then the second pass shows it building several stack objects whose vtables come from globals through
`[rip + 0xA061FB]`, `[rip + 0xA05696]`, `[rip + 0xA05F19]` and friends, and calling a long chain:

    2BC2 0x944530   2C2B 0x9454D0   2C50 0x87EDF0   2C60 0x9454D0   2C76 0x87D590
    2C92 0x9456A0   2CA2 0x1EE50    2CAD 0x5070E0   2CB9 0x5007C0   2CE7 0x87D8E0
    2CF0 0x8774F0

So the shape is: guard a critical section, fetch the engine, set a few string and numeric properties, then run a
sequence of calls over locally constructed objects. That is orchestration, not arithmetic: the arithmetic lives in the
callees, which is why the closure is the size it is.

## The order to take it

1. **Classify the library layer first.** Many of the 1208 are C++ runtime and library functions, as with every other
   closure walked so far. Each one read and classified collapses the map without any domain work. `re/g_closure_of.py 51`
   lists them leaves-first with their sizes.
2. **Implement the domain leaves**, bottom-up, each with the strongest evidence available: differential against the
   embedded original when the block is callable, behavioural otherwise, with every offset asserted.
3. **Re-run the closure after each batch** and watch the number fall. When it reaches zero, this export is done, and
   with it ordinals 51, 52, 164, 165, 216 and 217.
4. The wrappers 0x3310 and 0x3360 are already read whole, so they land as soon as 0x2AB0 does: they only save a field,
   set a flag, pass a constant and call it.

## Progress against this export

Nothing of 0x2AB0 is implemented yet. What is done is the terrain: the closure is enumerated, the head and the second
pass are read, the two wrappers are read, and the tool that orders the work exists.
