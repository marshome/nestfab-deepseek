# re/AGENT.md -- how to make an autonomous reverse engineering agent, and what this repository already has

## The question this answers

A long conversation with a model drifts: a new idea becomes the whole task and the earlier instructions become noise, because
nothing outside the conversation holds them. The fix is not a better prompt. It is to move the instructions, the state and the
discipline OUT of the conversation and into files a program reads, and then to make the model's output pass a gate before it
is believed. This file is the architecture, and this repository is a partial implementation of it.

## What a model is good at here, and what it is not

Good at: reading a body and saying what it does; recognising a shape; proposing where to look; writing the C++ once the
evidence is in.

Not good at: remembering thirty instructions at once; refusing its own plausible answer; knowing when two claims contradict;
staying on a worklist when a new idea arrives.

So the design puts the model where it is strong and gives it a program where it is weak. **The model proposes; the ledger and
the gate dispose.**

## The six components

### 1. A typed claim ledger -- the memory that cannot drift

`re/LEDGER.md` and `re/ledger.py`. Every claim carries a grade, a witness and a round:

    GUESS < SHAPE < ORACLE < INSTRUCTION < MEASURED < CONSTRUCTOR < DIFFERENTIAL

and the program REFUSES a claim used above its grade: a NAME needs an oracle (the module's own string) or a setter whose name
is the field's; a LAYOUT needs a constructor; an EQUIVALENCE needs the two implementations to agree when run. `promote`
refuses a grade that is not higher. This is the component that stops the drift, because the model's prose does not matter --
only what the ledger will accept does.

### 2. Extractors that emit PROPOSALS, never facts

Each one reads the binary and writes candidates with their evidence, into the ledger at `SHAPE`:

| extractor | what it proposes | file |
|---|---|---|
| the reporter channels | a function's own name, from the assertion or log string its call site loads | `re/g_assertions.py`, `re/g_harvest_names.py` |
| RTTI | a class, its slots, its member region | `re/g_whoami.py`, `re/g_own_class_list.py` |
| constructors | a complete layout, with size and widths | `re/g_ctor_fields.py` |
| setters | a field's name and offset, from the export that sets it | `re/g_ready_fields.py` |
| address derivations | an embedded sub-object's field set | `re/g_embedded_structs.py` |
| computed element sizes | a record type's size and leading fields | `re/g_element_50.py` |
| serialisers | the vocabulary of the JSON, as a lead | `re/g_json_fields.py` |

### 3. Verifiers that can only be run, not argued with

A proposal becomes a claim only when a verifier passes, and every verifier is code:

    a store/load at an address          -> g_ctor_fields.py, g_members.py
    a string the module loads           -> g_labels.py, g_region_strings.py
    the vtable a constructor installs   -> g_class_sites.py
    the recovered code vs the original  -> the differential tests in lcns/tests
    the project's own invariants        -> re/gate.ps1 (build, ctest, recovery, arch, embeddings, coverage, acceptance)

### 4. A deterministic worklist -- the priority the model cannot lose

`re/g_domain_closure.py` computes what is left once library code is transparent, forward from the entry point, and prints it
in work order. `re/g_ready.py` prints the exports whose closures are empty. A round takes its task FROM THAT LIST, never from
the conversation. This is what "do not lose the earlier instructions" means mechanically.

### 5. A gate that must be green before anything is committed

`re/gate.ps1`, one command, sets its own environment, deletes stale test binaries, builds, runs 22 tests and five checks. The
model cannot commit a claim the gate refuses.

### 6. A commit per round, with the evidence in the message

Sixty-odd commits so far, each naming the addresses and the round. The history IS the audit trail, and it is what a fresh
session reads instead of a conversation.

## The loop, exactly

    read the ledger and the worklist          -> one task, with its reason
    run the extractor for that task           -> proposals, at SHAPE
    run the verifier                          -> promote to INSTRUCTION, ORACLE, MEASURED or CONSTRUCTOR
    write the C++ or the document             -> the deliverable
    run the gate                              -> green or reverted
    commit                                    -> with the addresses
    update the ledger and the checkpoint      -> so the next round starts from the state, not the history

Around it: `re/RESUME.md` holds the rules and a checkpoint, and a rule this session added is that the human is synced every
thirty rounds rather than every round, because a report per round is itself a drift.

## Why this works where a conversation fails

* the state is a FILE, so a new session has it
* the priority is COMPUTED, so a new idea cannot displace it
* the grades are TYPED, so a plausible answer is refused at the point of use
* the gate is EXECUTED, so a wrong claim cannot be committed
* the model is only asked to do what it is good at

The failure mode to design against is not a lazy model. It is a CONFIDENT one: every defect in this repository's history was a
claim that looked exactly like a good answer, and the ledger exists because of that, not because of a lack of ideas. Six of
them are listed in `re/LEDGER.md`.

## What is missing, in priority order

1. **The prioritizer.** A program that reads the ledger and the worklist and picks the next task with its reason, so the
   choice is not made in a conversation. Everything it needs exists; what is missing is the ranking between "promote a SHAPE",
   "implement a ready export", "read a closure leaf" and "answer a gate failure".
2. **The loop driver.** A script that runs extractor -> verifier -> gate -> commit without a human turn, stopping on any gate
   failure. `re/gate.ps1` is already the hard part.
3. **A contradiction check.** Two claims that cannot both hold -- an offset with two widths, a function with two class slots, a
   layout whose fields do not sum to its size -- are detectable with what is already in the ledger, and none is checked yet.
4. **Sub-structure promotion.** The four `SHAPE` claims in the ledger (the sub-object at parent +0x40, the 0x50 byte element,
   the ToJson pairing, the strategy Run bodies) each need their own verifier to reach `CONSTRUCTOR`.

## On third-party tools

None is used and none is needed. `pefile` reads the image, `capstone` decodes instructions, and both are libraries rather than
a disassembler IDE; the whole analysis is Python over the bytes plus a C++ project that the differential tests can run. An
interactive disassembler would add a GUI and a database, and neither is where the difficulty is: the difficulty is that a
structure is found in its CONSTRUCTOR, a name is found in the module's own STRING, and a claim is worth exactly what its
witness can support.
