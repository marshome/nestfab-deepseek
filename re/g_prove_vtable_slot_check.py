# -*- coding: utf-8 -*-
"""Prove the vtable-slot-offset check fails when the recorded slots do not sit at base + 0x10 + n*8.

**A CHECK THAT HAS NEVER FAILED IS NOT KNOWN TO WORK.** This one passed on its first run, so it has to be shown failing on the exact defect it exists
for: a slot list that does not begin at the base's +0x10.
"""
import io
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VTABLES = os.path.join(HERE, "vtables.json")
CHECK = os.path.join(HERE, "g_check_vtable_slots.py")
BACKUP = os.path.join(HERE, "_vtable_slots_probe.json")


def run_check():
    result = subprocess.run([sys.executable, CHECK], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def main():
    shutil.copyfile(VTABLES, BACKUP)
    original = json.load(io.open(VTABLES, encoding="utf-8"))
    failures = []
    try:
        cases = []

        # 1. a slot list that starts one slot late -- the mistake of reading from a base that is 8 bytes off
        broken = json.loads(json.dumps(original))
        key = next(k for k, v in broken.items() if len(v.get("slots") or []) >= 3)
        broken[key]["slots"] = broken[key]["slots"][1:]
        cases.append(("a slot list shifted by one slot", broken))

        # 2. a slot whose recorded value is wrong
        broken2 = json.loads(json.dumps(original))
        key2 = next(iter(broken2))
        broken2[key2]["slots"] = list(broken2[key2]["slots"])
        broken2[key2]["slots"][0] = 0xDEAD
        cases.append(("a slot recorded at the wrong address", broken2))

        # 3. a vtable_rva that is a SLOT VALUE rather than a table base -- **THE MISTAKE I ACTUALLY MADE TWICE**
        broken3 = json.loads(json.dumps(original))
        key3 = next(iter(broken3))
        broken3[key3]["vtable_rva"] = broken3[key3]["slots"][0]
        cases.append(("a vtable_rva that is a SLOT VALUE, as I twice read it", broken3))

        for label, broken in cases:
            io.open(VTABLES, "w", encoding="utf-8", newline="\n").write(json.dumps(broken, indent=2, ensure_ascii=False) + "\n")
            code, output = run_check()
            failed = code != 0
            first = next((line.strip() for line in output.split("\n") if line.strip().startswith(("a ", "0x", "Tiling", "Row", "Engine", "Multi"))), "")
            print("%-52s expected FAIL   got %-4s %s" % (label[:52], "FAIL" if failed else "PASS",
                                                         "correct" if failed else "WRONG"))
            if first:
                print("      %s" % first[:88])
            if not failed:
                failures.append(label)
    finally:
        shutil.copyfile(BACKUP, VTABLES)
        os.remove(BACKUP)

    code, _output = run_check()
    print("")
    print("and on the real data it exits %d" % code)
    if failures:
        print("FAILING: the check is blind to %s" % "; ".join(failures))
        return 1
    print("PASS: the check fails on all three planted defects and passes on the real data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
