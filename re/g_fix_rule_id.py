# -*- coding: utf-8 -*-
"""Fix a rule id that the note tool derived from Chinese text.

re/g_note.py builds a rule's id with `[^a-z0-9]+ -> -`, which on Chinese text collapses to whatever digits the text contains. It
has now produced the id "30" TWICE -- once for the cadence rule and once for the reporting-density rule -- and both times
`rules-have-checks` caught it, which is the meta-check earning its place for the fourth time.

The repair is mechanical and the tool's deficiency is recorded rather than patched away, because the next Chinese requirement will
produce another such id and it should be recognised rather than puzzled over.
"""
import io
import re
import sys

PATH = r"D:\Nesting\nestfab\re\RULES.md"


def main(argv):
    new_id = argv[0] if argv else "report-density"
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    # find ids that are not a readable name: all digits, or shorter than four characters
    bad = []
    for match in re.finditer(r'\{"id":\s*"([^"]+)"', text):
        identifier = match.group(1)
        if identifier.isdigit() or len(identifier) < 4:
            bad.append(identifier)
    if not bad:
        print("no unreadable rule id found")
        return 0
    for identifier in bad:
        text = text.replace('{"id": "%s",' % identifier, '{"id": "%s",' % new_id)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("replaced %d unreadable id(s) %s with %r" % (len(bad), bad, new_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
