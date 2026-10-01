"""One more level up from the Row::Squeezer construction path, to name the engine entry."""
import sys

sys.path.insert(0, r"D:\Nesting\nestfab\re")
from lib import *  # noqa: E402
from capstone.x86 import X86_OP_IMM  # noqa: E402

try:
    from g1_names import NAMES  # noqa: E402
except Exception:
    NAMES = {}

PROF = load_prof()


def name_of(rva):
    return NAMES.get(rva) or (PROF.get(rva, {}) or {}).get("name") or ""


def callers_of(target, depth, seen=None, out=None, indent=0):
    if seen is None:
        seen, out = set(), []
    if target in seen or depth < 0:
        return out
    seen.add(target)
    for rva in sorted(PROF):
        try:
            for ins in disasm(rva):
                if (ins.mnemonic == "call" and ins.operands
                        and ins.operands[0].type == X86_OP_IMM and ins.operands[0].imm == target):
                    out.append((rva, ins.address, depth))
                    callers_of(rva, depth - 1, seen, out)
                    break
        except Exception:
            continue
    return out


for root in (0x6AABC0, 0x134470, 0x136B20, 0x13C380):
    prof = PROF.get(root) or {}
    print()
    print("=== climbing from 0x%x %s size=%s nins=%s" % (root, name_of(root), prof.get("size"),
                                                         prof.get("nins")))
    for f, s, d in callers_of(root, 3)[:20]:
        print("      depth%d 0x%-8x %-26s size=%-6s (call @0x%x)"
              % (3 - d, f, name_of(f), (PROF.get(f) or {}).get("size"), s))
