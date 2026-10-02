# -*- coding: utf-8 -*-
"""Rename the generated header and its namespace to what the evidence supports.

The previous round established the direction: RE 0x4EC00 initialises an object by calling RE 0x4E5B0, walks a container reached at
[rdx+0x18], and for each element reads a value at [rdi+0x40] and stores it into the object under a name. So the 107 entries are a REPORT
of observed values against the module's labels, and calling them "config parameters" was my inference rather than the module's statement.

The offsets and the strings are unchanged. Only the NAME of the file and of the namespace changes, because a name that asserts more than
the evidence is the defect this project's grades exist to prevent -- and a header called config_parameters.hpp tells every later reader
that a configuration has been recovered.
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "g_gen_config.py")

OLD_HEADER = "// lcns/include/lcns/config_parameters.hpp -- the nesting engine's parameters, each with the name the module uses."

NEW_HEADER = """// lcns/include/lcns/parameter_report.hpp -- the 107 fields RE 0x4EC00 writes, each under a name the module uses.
//
// NAMED FOR WHAT THE EVIDENCE SUPPORTS, and renamed once already. The first version called this a configuration with "parameters", which
// was an INFERENCE: the names and the offsets are the module's, but the direction is a REPORT. RE 0x4EC00 initialises an object by
// calling RE 0x4E5B0, walks a container reached at [rdx+0x18], and for each element reads a value at [rdi+0x40] and stores it into the
// object under a name. So it records values against the module's labels rather than applying settings.
//
// The offsets and the strings stand as recorded; only the interpretation changed, and this file name says which is which."""


def main():
    text = io.open(GEN, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if OLD_HEADER in text:
        text = text.replace(OLD_HEADER, NEW_HEADER, 1)
        print("header comment updated")
    text = text.replace("config_parameters.hpp", "parameter_report.hpp")
    text = text.replace("namespace config {", "namespace parameters {")
    text = text.replace("config::k", "parameters::k")
    text = text.replace("}  // namespace config", "}  // namespace parameters")
    io.open(GEN, "w", encoding="utf-8", newline="\n").write(text)

    if "config::k" in text or "config_parameters" in text:
        print("LEFTOVERS remain:")
        for needle in ("config::k", "config_parameters", "namespace config"):
            if needle in text:
                print("   %s" % needle)
        return 2
    print("generator now writes parameter_report.hpp under namespace parameters, with no leftovers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
