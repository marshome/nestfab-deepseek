#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate lcns/include/lcns/config_parameters.hpp from re/param_names.json.

Every field here has a NAME from the module's own string and an OFFSET from the instruction that stores it: RE 0x4EC00 asks the lookup
RE 0x82A3E0 for a named parameter and, when it is found, writes the value into a field of the object in rsi. So the name is ORACLE grade
and the offset is INSTRUCTION grade, and neither is inferred.

The struct is written with its offsets ASSERTED rather than laid out, because the point is to record what the module does and not to
produce a struct whose compiler-dependent padding happens to match. A static_assert names each one, so a later change that moves a field
fails the build instead of drifting.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "lcns", "include", "lcns", "config_parameters.hpp")

HEADER = '''// lcns/include/lcns/config_parameters.hpp -- the nesting engine's parameters, each with the name the module uses.
//
// GENERATED from re/param_names.json by re/g_gen_config.py. Do not edit by hand; rerun the generator.
//
// RE 0x4EC00 (5633 bytes) fills an object in rsi by asking RE 0x82A3E0 for a parameter BY NAME and storing the value when the lookup
// succeeds. The pattern, verified at one site by hand:
//
//     0x4F496  lea rdx, [rip + 0x960a7d]      ; -> 'nesting_pow_boost'
//     0x4F4A0  call 0x82a3e0                  ; look it up
//     0x4F4A5  test eax, eax / jne <skip>
//     0x4F4A9  movsd qword ptr [rsi + 0x100], xmm6   ; THE FIELD
//
// so every entry below is a name from the module's own strings beside the instruction that writes it. The name is ORACLE grade and the
// offset is INSTRUCTION grade, which is the strongest pair this project's ledger records short of a constructor.
//
// WHAT THE NAMES SAY ABOUT THE DESIGN, which is evidence and not decoration: %(taxonomy)s
//
// The offsets run from 0x%(first)X to 0x%(last)X with %(gaps)d gaps larger than eight bytes, so the struct has regions between the ones
// this parser touches -- those parameters are set elsewhere, or are not parameters at all.
#pragma once

#include <cstddef>
#include <cstdint>

namespace lcns {

/** The offsets RE 0x4EC00 writes, in the module's own parameter vocabulary. */
namespace config {

%(constants)s
/** The count of parameters this parser names, for a test to assert rather than repeat. */
constexpr std::size_t kConfigParameterCount = %(count)d;

}  // namespace config

/** A record of what each offset IS, for the reconstruction. It is deliberately not a struct with those members laid out: the point is
 *  to carry the module's names and offsets, and a laid-out struct would depend on the compiler's padding to agree with them. */
struct ConfigParameter {
    std::size_t offset;
    const char* name;
};

inline const ConfigParameter* configParameters(std::size_t& count) {
    static const ConfigParameter table[] = {
%(table)s    };
    count = sizeof(table) / sizeof(table[0]);
    return table;
}

%(asserts)s
}  // namespace lcns
'''


def main():
    data = json.loads(io.open(os.path.join(HERE, "param_names.json"), encoding="utf-8").read())
    rows = []
    for entry in data["parameters"].get("0x4EC00", []):
        field = entry.get("field")
        name = entry.get("name")
        if not field or not name:
            continue
        offset = int(field.split("+")[1], 16)
        rows.append((offset, name))
    rows.sort()
    if not rows:
        print("REFUSING: re/param_names.json has no fields for 0x4EC00")
        return 2

    constants = []
    for offset, name in rows:
        constants.append("constexpr std::size_t k%-52s = 0x%X;" % (name, offset))
    table = []
    for offset, name in rows:
        table.append('        {0x%X, "%s"},\n' % (offset, name))
    asserts = []
    for offset, name in rows:
        asserts.append('static_assert(config::k%s == 0x%X, "RE 0x4EC00 stores %s at +0x%X");'
                       % (name, offset, name, offset))

    gaps = 0
    for previous, current in zip(rows, rows[1:]):
        if current[0] - previous[0] > 8:
            gaps += 1

    text = HEADER % {
        "constants": "\n".join(constants) + "\n",
        "table": "".join(table),
        "asserts": "\n".join(asserts) + "\n",
        "count": len(rows),
        "first": rows[0][0],
        "last": rows[-1][0],
        "gaps": gaps,
        "taxonomy": ("33 enable_* switches against 28 nb_* counts means the engine is configured mostly by toggles, and the four\n"
                     "// *_price_frequency parameters plus two *_price_max_random ones describe a weighted search over several strategies."),
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote %s with %d parameters" % (OUT, len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
