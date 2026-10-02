# Operations that were accessor-shaped and are not yet types

These seven were in lcns/include/lcns/field_accessors.hpp, and their names say what they DO -- which is why they are worth keeping as
WORK rather than as the memcpy wrappers they were. **Each acts on an object that has to be identified before it can be a method**, and the
wrappers they were built from are deleted.

| operation | RE | what the name says |
|---|---|---|
| constructCandidate_22E30 | 0x22E30 | builds a candidate from an order, a double and an int |
| constructCandidate_22A20 | 0x22A20 | the same, a second entry |
| moduleSwitch_1BF00 | 0x1BF00 | the module's enable/disable; see lcns/module_switch.hpp for what is already recovered |
| engineFetch_1BF40 | 0x1BF40 | fetches an engine out of the module |
| initEmptyContainer_51BFC0 | 0x51BFC0 | initialises an empty container |
| notNullMember_822590 | 0x822590 | tests a member for non-null |
| assignTimer_5F3900 | 0x5F3900 | assigns a timer; it calls timerObject_5F47C0, which is why the split failed |

**AND THE LESSON THE SPLIT TAUGHT**: the semantic functions are WRAPPERS AROUND the trivial ones, so the two cannot be separated. The
right form is neither a header of 96 memcpy wrappers nor seven functions calling them -- it is each function placed in the class whose
object it acts on.
