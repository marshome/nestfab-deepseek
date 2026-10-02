# -*- coding: utf-8 -*-
"""Delete the whole field-accessors SECTION of test_boxacc.cpp, from its heading to the end of the file.

EVERY BLOCK IN IT WAS A TAUTOLOGY EVEN BEFORE THE ACCESSORS WERE DELETED: each wrote a value into a local buffer with memcpy and read it back
with memcpy, or the reverse. **It proved memcpy**, and the accessors it was written for are gone. Removing the blocks one at a time left the
assertions behind; removing the section is what the situation calls for.
"""
import io
import re
import sys

TEST = r"D:\Nesting\nestfab\lcns\tests\test_boxacc.cpp"


def main():
    text = io.open(TEST, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    # the first heading that mentions the accessors, and everything after it up to the closing brace of main
    match = re.search(r"^    // -{10,} (?:the field accessors|field accessors)[^\n]*$", text, re.M)
    if not match:
        print("no accessor section heading found")
        return 1
    start = match.start()
    tail = text.rfind("}")            # the file's final brace
    replacement = (
        "    // ------------------------------------------------------------------ the field accessors, SECTION DELETED\n"
        "    //\n"
        "    // Several hundred lines stood here checking 96 generated accessors against their own offsets. **Every block was a tautology**:\n"
        "    // it wrote a value into a local buffer with memcpy and read it back with memcpy, so it proved memcpy and not the module. The\n"
        "    // accessors are deleted with lcns/field_accessors.hpp, their offsets and RVAs are in re/all_class_fields.json and the ledger, and\n"
        "    // the operations among them that HAD a name are recorded as work in re/pending_operations.md.\n\n")
    text = text[:start] + replacement + text[tail:]
    io.open(TEST, "w", encoding="utf-8", newline="\n").write(text)
    print("deleted the accessor section; test_boxacc.cpp is now %d lines" % text.count("\n"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
