# -*- coding: utf-8 -*-
"""Give engines_composite.hpp the class it names five times, and record the pattern the checker found.

The checker reports 17 places where a header names one of the module's own classes more than once and declares it nowhere. Nine of those
are the same defect the human found in engines.hpp, and it is a repository-wide pattern rather than one round's slip -- so this fixes the
one the round touched and records the rest as a measured list rather than leaving them to be discovered one at a time.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HEADER = os.path.join(ROOT, "lcns", "include", "lcns", "engines_composite.hpp")
LEDGER = os.path.join(HERE, "ledger.json")

CLASS = '''
// ------------------------------------------------------------------------------------------------
// THE CLASS ITSELF, declared rather than described.
//
// A header that names a class five times and declares it nowhere is the defect the human found in engines.hpp: a reader -- and a commit
// message -- can take constants for a definition. So CompositeEngine is declared here with what is known: it is an Engine, its Run is
// 0x759B70, and it holds the count and the stride its prologue computes. **No member is invented beyond those two**, because the vtable
// says nothing about a class's data.

/** Engine::CompositeEngine, Run at 0x759B70, vtable 0xA3D000.
 *
 *  THE NAME DOES NOT DESCRIBE THE BEHAVIOUR. Its Run calls NO other engine's Run -- the six addresses it does not call are listed below --
 *  and instead walks a container of 16 byte records reached through its second argument's +0x10 and +0x18, accumulating into locals.
 */
class CompositeEngine : public EngineBase {
public:
    CompositeEngine() = default;

    /** RE 0x759BAA: `sar rax, 4`, so the count is the range divided by the stride. */
    static std::size_t elementCount(std::size_t begin, std::size_t end) {
        return compositeElementCount(begin, end);
    }

    void* run(const void* problem, double timeLimit, void* observer, void* result) override;

private:
    // RE 0x759BBC: the eight quadwords its prologue zeroes are LOCALS, not members -- they live at rsp+0xe0 upward. The only thing this
    // class is known to hold is the container it walks, and that belongs to the Problem its Run is handed rather than to the engine, so
    // there is nothing to put here yet and saying so is more useful than a placeholder.
};

'''


def main():
    text = io.open(HEADER, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if "class CompositeEngine" in text:
        print("already declared")
    else:
        marker = "}  // namespace lcns"
        assert marker in text, "the namespace close is gone"
        text = text.replace(marker, CLASS.strip("\n") + "\n\n" + marker, 1)
        io.open(HEADER, "w", encoding="utf-8", newline="\n").write(text)
        print("CompositeEngine declared in engines_composite.hpp")

    data = json.loads(io.open(LEDGER, encoding="utf-8").read())
    if not any(c["subject"] == "classes.named-without-being-declared" for c in data["claims"]):
        data["claims"].append({
            "grade": "MEASURED",
            "kind": "constant",
            "subject": "classes.named-without-being-declared",
            "predicate": ("17 places name one of the module's own classes more than once in a hand-written header and declare it nowhere, "
                          "which is a repository-wide pattern and not one round's slip"),
            "witness": ("re/g_defined_classes.py, after excluding substituted template parameters: engines_composite.hpp 1, nester.hpp 3, "
                        "recovery.hpp 7, row.hpp 1, engine.hpp 3, engines.hpp 1, model.hpp 1 -- including Multi::NestingNester, "
                        "Multi::SplitNode, Multi::TerminalNode, Row::Squeezer and Compact::Compacter::Implementation"),
            "round": 656,
        })
        io.open(LEDGER, "w", encoding="utf-8", newline="\n").write(json.dumps(data, indent=1, sort_keys=True))
        print("recorded the pattern as a MEASURED claim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
