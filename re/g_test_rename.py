# -*- coding: utf-8 -*-
"""Point the test at lcns/parameter_report.hpp and the renamed namespace."""
import io

PATH = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"

PAIRS = [
    ("#include \"lcns/config_parameters.hpp\"", "#include \"lcns/parameter_report.hpp\""),
    ("lcns::config::", "lcns::parameters::"),
    ("lcns::ConfigParameter", "lcns::ParameterReportEntry"),
    ("configParameters", "parameterReport"),
    ("// RE 0x4EC00 fills an object in rsi by asking 0x82A3E0 for a parameter BY NAME",
     "// RE 0x4EC00 READS a value at [rdi+0x40] and records it under a parameter name"),
]


def main():
    text = io.open(PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    changed = 0
    for old, new in PAIRS:
        if old in text:
            text = text.replace(old, new)
            changed += 1
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(text)
    print("applied %d of %d substitutions" % (changed, len(PAIRS)))
    for needle in ("config_parameters", "lcns::config::", "ConfigParameter"):
        if needle in text:
            print("LEFTOVER: %s" % needle)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
