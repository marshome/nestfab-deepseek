# -*- coding: utf-8 -*-
"""Debug what g_class_slot_offsets.py's matcher actually sees, on NoFillNester's slot 5.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

source = io.open(os.path.join(HERE, "g_class_slot_offsets.py"), encoding="utf-8").read()
source = source.replace("sys.exit(main(sys.argv[1:]))", "pass")
namespace = {"__file__": os.path.join(HERE, "g_class_slot_offsets.py"), "__name__": "probe"}
exec(compile(source, "g_class_slot_offsets.py", "exec"), namespace)

from lib import disasm, load_prof  # noqa: E402

STORE = namespace["STORE"]
profile = load_prof()
reads, writes = namespace["slot_offsets"](0x7F240, profile)
print("the function returns reads %s writes %s" % (
    " ".join("+0x%X" % o for o in sorted(reads)) or "none",
    " ".join("+0x%X" % o for o in sorted(writes)) or "none"))
print("")
print("the first 16 instructions, with what STORE matches:")
for instruction in disasm(0x7F240, count=16):
    print("   %06X %-12s %-40s store=%s" % (instruction.address, instruction.mnemonic,
                                            instruction.op_str[:40], bool(STORE.match(instruction.op_str))))
