# Export implementations

What stands behind each exported entry point, and what the claim rests on. `forwardedCount()` is the number of entries
whose behaviour is implemented. Every other entry reports the call and returns the documented neutral value, with its
original bytes embedded and verified against the module by `re/check_embeddings.py`.

| Entry (ordinals) | rva | Recovered behaviour | Held to the assembly by |
|---|---:|---|---|
| `GetNumberOfNestings` (25/26) | `0xB0C0` | element count, 312-byte stride, container at +0x50/+0x58 | behavioural test; the multiply is the modular inverse of 39 |
| `GetNumberOfNestedParts` (23/24) | `0xB190` | the same over `[+8]+0x28`, stride 120 | behavioural test; inverse of 15 |
| `GetMultiplicity` (17/18) | `0xB100` | 32-bit field at `[+8]+0x20` (via `0x51D090`) | behavioural test |
| `GetPartUserString` (27/28) | `0xC5E0` | pointer at +0x1B8 | behavioural test |
| `GetSolution` (33/34) | `0xB0A0` | identity: returns its argument, no memory touched | behavioural test |
| `sub_16CF0` (210/211) | `0x16CF0` | pointer at +0x1B8, without the logger call | behavioural test |
| `sub_AFF0` (288/289) | `0x0AFF0` | byte +0xF8 = (arg != 0) | behavioural test |
| `sub_B000` (286/287) | `0x0B000` | double at +0x100, byte +0xF9 = (arg != 0) | behavioural test |

## Why these cannot be compared by running the original

Each begins by passing a RIP-relative label string to the logger, or is reached only through a fragment that does, so the
embedded copy cannot execute from a different image address. They are therefore established by **behavioural** tests built
from the decoded field offsets and instruction sequence, each expectation computed by hand and printed by the test.

## Deliberately not implemented, with the reason

| Entry (ordinals) | rva | Why not |
|---|---:|---|
| `sub_AFE0` (270/271) | `0x0AFE0` | a thunk: `setne cl; movzx ecx,cl; jmp 0x1B270`. It converts its first argument to a boolean and tail-calls `0x1B270`, whose behaviour is not recovered. Writing the thunk without the callee would do nothing or invent the callee's effect. |
| `GetBuildVersion` (88/89) | `0x0B490` | returns the pointer held in the MODULE's global at rva `0xAB7660` -- data owned by the original image. A reimplementation cannot return that address, and what it should return instead is a semantics decision, not a decoding one. |

## Side effects not reproduced

Several entries log through `dbg::symlog` before doing their work. Logging is a toolchain facility, not domain behaviour,
and it affects no return value; it is not reproduced. Where an entry's only effect beyond logging is a return value, that
value is reproduced exactly.
