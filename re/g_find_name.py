# -*- coding: utf-8 -*-
"""Search every string in the image and every document in the repository for a name, and say plainly what was found.

Usage: python g_find_name.py liblcns_52 [--docs]

A question about a name -- "do you know liblcns_52" -- has three possible answers and they must be distinguished rather than
blurred: the name is in the image, the name is in this repository, or the name exists nowhere in either. This prints which, with
the addresses or the files, so the answer is checkable instead of remembered.
"""
import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import lib as LIB  # noqa: E402


def main(argv):
    if not argv:
        print("give a name")
        return 2
    needle = argv[0]
    blob = LIB.data() if callable(getattr(LIB, "data", None)) else LIB.data

    hits = [m.start() for m in re.finditer(re.escape(needle.encode()), blob)]
    print("in the image: %d hit(s)%s" % (len(hits), (" " + ", ".join("0x%X" % h for h in hits[:8])) if hits else ""))
    for hit in hits[:3]:
        end = blob.find(b"\x00", hit)
        print("    0x%X  %r" % (hit, blob[max(0, hit - 40):end][:120]))

    # every printable string containing a fragment of the name, which is how a mangled or suffixed spelling is found
    fragment = needle.split("_")[0]
    related = set()
    for match in re.finditer(rb"[\x20-\x7e]{4,}", blob):
        text = match.group(0).decode("ascii", "replace")
        if fragment.lower() in text.lower() and len(text) < 90:
            related.add(text)
    print("")
    print("strings in the image containing %r: %d" % (fragment, len(related)))
    for text in sorted(related)[:20]:
        print("    %s" % text)

    print("")
    found_files = []
    for path in glob.glob(os.path.join(ROOT, "**", "*"), recursive=True):
        if not os.path.isfile(path) or os.path.getsize(path) > 4 << 20:
            continue
        if os.sep + ".git" + os.sep in path or os.sep + "backup" + os.sep in path:
            continue
        try:
            text = io.open(path, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        if needle in text:
            found_files.append(os.path.relpath(path, ROOT).replace("\\", "/"))
    print("in the repository: %d file(s)" % len(found_files))
    for name in sorted(found_files)[:25]:
        print("    %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
