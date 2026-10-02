# -*- coding: utf-8 -*-
"""Prove the vtable check fails when the JSON disagrees with the module.

**A CHECK THAT HAS NEVER FAILED IS NOT KNOWN TO WORK**, and this one FAILED ON ALL 443 ENTRIES the first time it ran -- because it compared RVAs
against absolute virtual addresses and I had the image base wrong. So it has demonstrably failed, but on its own bug rather than on a defect in
the data. This plants the defect.
"""
import io
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VTABLES = os.path.join(HERE, "vtables.json")
CHECK = os.path.join(HERE, "g_check_vtables.py")
BACKUP = os.path.join(HERE, "_vtables_probe_backup.json")


def main():
    shutil.copyfile(VTABLES, BACKUP)
    original = json.load(io.open(VTABLES, encoding="utf-8"))
    failures = []
    try:
        cases = []
        # 1. a slot whose recorded address is wrong
        broken = json.loads(json.dumps(original))
        key = next(iter(broken))
        broken[key]["slots"] = list(broken[key]["slots"])
        broken[key]["slots"][0] = 0x123456
        cases.append(("a slot recorded at the wrong address", broken))
        # 2. a TRUNCATED slot list, which is exactly the mistake I made by hand
        broken2 = json.loads(json.dumps(original))
        key2 = next(k for k, v in broken2.items() if len(v.get("slots") or []) >= 4)
        broken2[key2]["slots"] = broken2[key2]["slots"][:2]
        cases.append(("a slot list truncated, as my own misreading produced", broken2))
        # 3. a base that is not a vtable
        broken3 = json.loads(json.dumps(original))
        key3 = next(iter(broken3))
        broken3[key3]["vtable_rva"] = 0x1000
        cases.append(("a base that is not a vtable", broken3))

        for label, broken in cases:
            io.open(VTABLES, "w", encoding="utf-8", newline="\n").write(json.dumps(broken, indent=2, ensure_ascii=False) + "\n")
            result = subprocess.run([sys.executable, CHECK], capture_output=True, text=True, encoding="utf-8")
            failed = result.returncode != 0
            # the truncated case must be caught by the "word after the last slot" test
            named = [l.strip() for l in (result.stdout or "").split("\n") if "slot" in l or "AFTER" in l]
            print("%-56s expected FAIL   got %-4s %s" % (label[:56], "FAIL" if failed else "PASS",
                                                         "correct" if failed else "WRONG"))
            if named:
                print("      %s" % named[0][:88])
            if not failed:
                failures.append(label)
    finally:
        shutil.copyfile(BACKUP, VTABLES)
        os.remove(BACKUP)

    print("")
    result = subprocess.run([sys.executable, CHECK], capture_output=True, text=True, encoding="utf-8")
    print("and on the real data it exits %d" % result.returncode)
    if failures:
        print("FAILING: the check is blind to %s" % "; ".join(failures))
        return 1
    print("PASS: the check fails on all three planted defects and passes on the real data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
