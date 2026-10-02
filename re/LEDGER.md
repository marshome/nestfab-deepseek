# re/LEDGER.md -- the claim ledger: what this project believes, and the witness for each belief

## Why this file exists

A reverse engineering session forgets. The model that reads this repository next will not see the conversation that produced
these claims, and a claim without its witness is indistinguishable from a guess that happened to be written down. Every
round this project has lost time to exactly that: an offset-frequency count that claimed an object was a kilobyte because the
numbers kept coming, a naming tool that stamped one name on twenty fields because a big function writes twenty offsets, a
mangled-name decoder that mislabelled fifty standard library classes as this module's own, a layout generator that dropped a
field while reporting the field as named.

None of those was a search failure. Each was a CLAIM that no mechanism could refuse.

So every claim lives here with the strength of the evidence it actually has, and nothing is allowed to be used at a strength
above its evidence. The vocabulary is deliberately small, because a taxonomy with twenty grades is a taxonomy nobody applies.

## The grades, weakest to strongest

| grade | meaning | what may be done with it |
|---|---|---|
| `GUESS` | a hunch with no instruction behind it | nothing. It is written down so it is not re-derived, and it is never cited as a reason |
| `SHAPE` | a pattern that matches, with no second witness | may guide where to read next; may NOT name a field or fix a layout |
| `ORACLE` | the module's own words: an assertion string, a log label, an export name, a serialiser key | may NAME things, and the name carries the address of the string |
| `INSTRUCTION` | a specific store, load or comparison at a specific address, quoted | may fix an offset, a width or a branch, and the claim carries the address |
| `MEASURED` | a number read out of the binary: a constant, a size, an allocation | may be used as a value, with the address it was read from |
| `CONSTRUCTOR` | a function that writes every field of an object, read whole | fixes the object's SIZE and its complete field list. The strongest evidence for a layout |
| `DIFFERENTIAL` | the recovered code and the original agree when both are RUN | may be cited as behaviour, and it is the only grade that justifies saying "equivalent" |

`CONSTRUCTOR` outranks `INSTRUCTION` for a layout and it took two rounds to accept that: the offset-frequency tools produced a
confident and wrong answer, and one constructor (`0x14620 NewLaunchingOrder`, allocating 0x2C0 and writing 96 fields) settled
the question in four instructions. **A structure is found in its constructor, not in the frequency of its offsets.**

## The rules that use the grades

1. A field may carry a NAME only from `ORACLE`, or from `INSTRUCTION` where the instruction is a setter whose own name is the
   field's. Two independent witnesses are preferred, and the count is recorded next to the name. Twenty-six of the launch
   order's 96 fields clear that bar; the rest keep an offset-derived name and say so.
2. A layout may be declared only from `CONSTRUCTOR`, and its size assertion comes from the allocation.
3. A branch may be declared equivalent only from `DIFFERENTIAL`.
4. A `SHAPE` may propose, never conclude. Its proposals are written here as `SHAPE` until an instruction or an oracle
   promotes them.
5. A claim whose evidence is in a file records the FILE AND THE LINE, not the address alone: addresses move when a layout is
   regenerated and a line number plus a quoted fragment does not.

## The ledger

Filled by `re/g_ledger.py`. Each row: the claim, its grade, its witness, and the round it was established.

| claim | grade | witness |
|---|---|---|
| the launch order is 0x2C0 bytes | `CONSTRUCTOR` | RE 0x14620 allocates 0x2C0 and writes 96 fields, largest +0x2B8 |
| the launch order's field `automaticStop` is at +0x240 | `ORACLE` + `INSTRUCTION` | export `SetAutomaticStop` (140) stores there at RE 0xE0D9; RE 0x22BC1 reads the same offset |
| `multiplicityPreference` (+0x010) is a double | `INSTRUCTION` | RE 0xD255 and RE 0x14668 are both `movsd`; declaring it as an integer made the compiler insert a convert |
| the 0x48 byte node's string is owned iff its pointer is not the node's own +0x30 | `INSTRUCTION` | RE 0x9308C0 compares `+0x20` with `+0x30` before freeing |
| `0x9302C0` and `0x9308C0` are the node's copy and release | `DIFFERENTIAL` | `lcns/tests/test_recovered.cpp` runs both halves of the ownership rule |
| the module has 75 classes of its own | `MEASURED` | `re/vtables.json` filtered on the MANGLED name, not the decoded one |
| `Multi::RowNester`'s vtable is 0xA3BB30 | `MEASURED` | `re/vtables.json` slot 5 is `0x913E0`, the Run body `re/STRATEGY_METHODS.md` records |
| parent `+0x40` holds a sub-object with fields `+0x10..+0x38` | `SHAPE` | 15 functions derive its address with `lea`; no constructor read yet |
| the 0x50 byte element begins `+0x10 +0x18 +0x20` | `SHAPE` | 57 functions compute its address; several element registers per body contaminate the aggregate |
| `ToJson`'s keys name the solution's fields | `SHAPE` | the keys are `ORACLE`-grade strings but the key-to-offset pairing picks the wrong accessor |

The last three are `SHAPE` on purpose. They are the most promising leads in the repository and they are NOT allowed to name a
field or fix a layout until something promotes them, because each of them is exactly the kind of claim that cost a round
earlier.

## How a claim is promoted

    SHAPE -> ORACLE        read the string the module loads next to the offset
    SHAPE -> INSTRUCTION   read the store or the comparison that uses the offset, and quote it
    SHAPE -> CONSTRUCTOR   find the function that writes every field
    any   -> DIFFERENTIAL  run both implementations and compare

A promotion is recorded here with the round and the witness. A claim is never silently upgraded, and the three `SHAPE` rows
above are how the next round knows where to look.
