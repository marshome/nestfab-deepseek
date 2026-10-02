# -*- coding: utf-8 -*-
"""List the rules whose `check` names a script that no longer exists, and which rule names it.

The meta-check now verifies a check PATH against the filesystem, and it is reporting scripts that were deleted in earlier rounds while their
rules kept naming them. **That is the drift the meta-check exists to catch**, and this prints the pairs so each can be resolved.
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
text = io.open(os.path.join(HERE, "RULES.md"), encoding="utf-8", errors="replace").read()

params = re.findall(r'"check":\s*"([^"]+)"', text)
paths = [p for p in params if re.match(r"^re/[\w./_-]+\.(?:py|ps1)$", p)]
missing = sorted({p for p in paths if not os.path.exists(os.path.join(HERE, os.path.basename(p)))
                  and not os.path.exists(os.path.join(HERE, p))})

print("check scripts named but absent: %d" % len(missing))
for path in missing:
    print("   %s" % path)
print("")
print("the rules that name them:")
for block in re.finditer(r'\{"id":\s*"([^"]+)",(.*?)\n\n', text, re.S):
    rid, body = block.group(1), block.group(2)
    for path in missing:
        if path in body:
            why = ""
            m = re.search(r'"rule":\s*"([^"]{0,40})', body)
            if m:
                why = m.group(1)
            print("   %-44s -> %-28s %s" % (rid[:44], path, why))
