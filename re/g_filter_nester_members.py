# -*- coding: utf-8 -*-
"""Give FilterNester and the two structs the members the newly-read constructor and run actually establish.

THE MEMBERS, each from an instruction:

    FilterNester::rng_        RE 0xB3AB0: the 624 word state array based at +0x20, and RE 0xB3AC1 the index at +0x9E0
    FilterNester::draw        RE 0x609E20, the Bernoulli trial the run calls with the generator
    BeamParams::frequencyRatioSecondary  RE 0xB3B62: a double at +0x178, eight bytes past the one at +0x170 the class already names
    Solution::filterScore     RE 0xB3B6A: the double 0x97A090 produces and the run stores
"""
import io
import os
import re
import sys

ROOT = r"D:\Nesting\nestfab"
NESTER = os.path.join(ROOT, "lcns", "include", "lcns", "nester.hpp")
MODEL = os.path.join(ROOT, "lcns", "include", "lcns", "model.hpp")
SRC = os.path.join(ROOT, "lcns", "src", "nester.cpp")


def patch_nester():
    text = io.open(NESTER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    old = """class FilterNester : public Nester {
public:

    const char* name() const override { return "FilterNester"; }
    const char* tracePrefix() const override { return kTraceFilter; }   // RE verbatim
    double estimate(const SolveContext&) const override;
    Solution run(SolveContext&) override;
};"""
    new = """// RE 0xA3B4F0. **THE CLASS CARRIES A MERSENNE TWISTER**, seeded with the constant 1 by its constructor at 0xB3A87 and used by its Run as a
// coin: 0xB3B4F hands the generator to 0x609E20 with a probability out of the options, and 0xB3B6A hands it to 0x97A090. See
// lcns/src/filter_nester.cpp for the instructions.
class FilterNester : public Nester {
public:
    FilterNester();

    const char* name() const override { return "FilterNester"; }
    const char* tracePrefix() const override { return kTraceFilter; }   // RE verbatim
    double estimate(const SolveContext&) const override;
    Solution run(SolveContext&) override;

    /** RE 0x609E20: a Bernoulli trial that advances the generator it is given. */
    bool draw(double probability);

private:
    Mt19937 rng_;      // RE 0xB3AB0: the state at +0x20, and RE 0xB3AC1 the index at +0x9E0
};

/** RE 0x97A090, 1599 bytes, SEVENTEEN callers: it takes the generator and a double and produces a double. A free function, because three
 *  other nesters reach it and a member would claim it as one class's own. */
double filterScore(const SolveContext& ctx, Mt19937& rng);"""
    if old not in text:
        print("REFUSING: FilterNester's declaration is not as expected")
        return
    text = text.replace(old, new, 1)

    # the second probability, at +0x178, which the class names the first of
    if "frequencyRatioSecondary" not in text:
        text = text.replace("    double frequencyRatio = 1.0; // RE key \"beam_frequency_ratio\"",
                            "    double frequencyRatio = 1.0; // RE key \"beam_frequency_ratio\"\n"
                            "    double frequencyRatioSecondary = 0.0;   // RE 0xB3B62: a double at +0x178, eight bytes past the one above", 1)
    io.open(NESTER, "w", encoding="utf-8", newline="\n").write(text)
    print("FilterNester carries its generator and draw(); BeamParams carries the second probability")


def patch_model():
    text = io.open(MODEL, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "filterScore" in text:
        print("Solution already carries filterScore")
        return
    old = """struct Solution {
    std::vector<Nesting> nestings;
    bool valid = false;"""
    new = """struct Solution {
    std::vector<Nesting> nestings;
    bool valid = false;
    double filterScore = 0.0;      // RE 0xB3B6A: the double 0x97A090 produces, which FilterNester's Run stores"""
    if old not in text:
        print("REFUSING: Solution is not as expected")
        return
    io.open(MODEL, "w", encoding="utf-8", newline="\n").write(text.replace(old, new, 1))
    print("Solution carries filterScore")


def drop_old():
    text = io.open(SRC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    for signature in ("double FilterNester::estimate(const SolveContext& ctx) const {",
                      "Solution FilterNester::run(SolveContext& ctx) {"):
        start = text.find(signature)
        if start < 0:
            continue
        index = text.find("{", start)
        depth = 0
        while index < len(text):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    break
            index += 1
        end = index + 1
        while end < len(text) and text[end] in "\r\n":
            end += 1
        text = text[:start] + ("// FilterNester's estimate and run now live in lcns/src/filter_nester.cpp, beside the constructor's instructions.\n\n") + text[end:]
    io.open(SRC, "w", encoding="utf-8", newline="\n").write(text)
    print("removed the old FilterNester bodies from nester.cpp")


if __name__ == "__main__":
    patch_nester()
    patch_model()
    drop_old()
