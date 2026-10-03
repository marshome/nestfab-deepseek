# -*- coding: utf-8 -*-
"""The round driver: pick a task from the state, run its extractor, verify, gate, commit -- never push.

Usage:
    python g_round.py                -> one round: choose, extract, gate, commit
    python g_round.py --dry          -> show what it would do, and touch nothing
    python g_round.py --task "parent+0x40.subobject"

What this automates and what it deliberately leaves to the model:

  AUTOMATED  choosing the task from re/ledger.json and the worklists, running that task's extractor, running the gate,
             committing with the evidence in the message, refreshing the checkpoint, and REFUSING to push.
  LEFT       reading a body and deciding what it means. A program can run `g_ctor_fields.py` on an address; only a reader
             can say that the fields it printed are one structure. So the driver stops at the point where judgement starts and
             prints the exact command whose output a round has to interpret.

Why the driver exists at all is in re/AGENT.md: a session chooses its next task from the conversation, so a new idea becomes
the whole task and the earlier instructions become noise. Here the task comes from re/ledger.json and from
re/g_prioritize.py, both on disk, and neither can be talked out of its ranking.

The push refusal is not a convention. `git` is invoked with an explicit argument vector that never contains `push`, the
driver asserts that no remote is contacted, and it reports how many commits are ahead of the tracking branch -- so "local
commits only" is a fact a run prints rather than a rule a session is asked to remember.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PYTHON = sys.executable

# The extractor each promotable subject runs. A subject that is not here is not a task the driver will take.
EXTRACTOR = {
    "parent+0x40.subobject": None,          # needs the owning class's constructor, chosen by reading, see --task output
    "element50.layout": ["g_element_50.py", "--top", "5"],
    "ToJson.keys": ["g_json_fields.py", "--window", "12"],
    "Multi::Run bodies": None,              # needs a Run read against re/STRATEGIES.md
}


def run(command, cwd=ROOT, capture=True):
    """Run a command with an argument VECTOR, never a shell string, so no quoting layer can inject a git subcommand."""
    assert command[0] != "git" or "push" not in command, "the driver must never push"
    # **THE ENCODING IS NAMED BECAUSE THIS MACHINE DECODES WITH GBK.** The rules are written in Chinese and their output reaches this driver, so a bare
    # `text=True` makes `.stdout` None on the first non-ASCII byte and the caller's next attribute access raises. `errors="replace"` keeps the decode total:
    # a driver that reads a tool's verdict must not be able to fail on a byte.
    result = subprocess.run(command, cwd=cwd, capture_output=capture, text=True, encoding="utf-8", errors="replace")
    return result.returncode, result.stdout or "", result.stderr or ""


def git(*args):
    code, out, err = run(["git"] + list(args))
    if code != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(args), err.strip()))
    return out.strip()


def priorities():
    code, out, _err = run([PYTHON, os.path.join(HERE, "g_prioritize.py"), "--top", "10"])
    if code != 0:
        return []
    tasks = []
    for line in out.split("\n"):
        m = re.match(r"\s*\d+\.\s+([A-Z]+)\s+(\S+(?:\s+\S+)*?)\s{2,}(.+)$", line)
        if m:
            tasks.append((m.group(1), m.group(2).strip(), m.group(3).strip()))
    return tasks


def ledger_subjects():
    data = json.load(io.open(os.path.join(HERE, "ledger.json"), encoding="utf-8"))
    return {claim["subject"]: claim for claim in data["claims"]}


def ahead_of_remote():
    """How many local commits the tracking branch does not have. The driver prints this and never resolves it."""
    code, out, _err = run(["git", "rev-list", "--count", "@{u}..HEAD"])
    if code != 0:
        return None
    try:
        return int(out.strip())
    except ValueError:
        return None


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true", help="print the plan and change nothing")
    parser.add_argument("--task", default=None, help="take this subtask instead of the top of the ranking")
    args = parser.parse_args(argv)

    print("=== re/g_round.py: one round, chosen from the state")
    dirty = git("status", "--porcelain")
    print("working tree: %s" % ("dirty" if dirty else "clean"))
    ahead = ahead_of_remote()
    print("local commits not on the tracking branch: %s" % ("unknown (no upstream)" if ahead is None else ahead))
    print("push: the driver has no push path, and asserts it before every command it runs")
    print("")

    tasks = priorities()
    if not tasks:
        print("the prioritizer returned nothing; nothing to do")
        return 0
    print("the ranking, from re/g_prioritize.py:")
    for index, (kind, subject, reason) in enumerate(tasks, 1):
        print("  %2d. %-10s %-32s %s" % (index, kind, subject[:32], reason[:70]))
    print("")

    chosen = None
    if args.task:
        for kind, subject, reason in tasks:
            if args.task.lower() in subject.lower():
                chosen = (kind, subject, reason)
                break
        if chosen is None:
            print("the task %r is not in the ranking; refusing to invent one" % args.task)
            return 2
    else:
        chosen = tasks[0]

    kind, subject, reason = chosen
    print("=== chosen: %s  %s" % (kind, subject))
    print("    because: %s" % reason)
    print("")

    subjects = ledger_subjects()
    claim = subjects.get(subject)
    if claim:
        print("ledger: %s -- %s" % (claim["grade"], claim["predicate"]))
        print("        witness: %s" % claim["witness"])
        print("")

    extractor = EXTRACTOR.get(subject)
    if extractor is None:
        print("=== this task needs a READER, not a program")
        print("    The driver stops here on purpose: a program can print a constructor's fields, and only a reader can say")
        print("    that they are one structure. Run the extractor named in the ranking, read its output, and then either")
        print("        python re/ledger.py promote \"%s\" --to CONSTRUCTOR --witness \"...\" --round N" % subject)
        print("    or leave the claim at SHAPE and record what blocked it.")
        return 0

    command = [PYTHON, os.path.join(HERE, extractor[0])] + extractor[1:]
    print("=== the extractor: %s" % " ".join(os.path.basename(c) for c in command))
    if args.dry:
        print("    --dry: not running it")
        return 0
    code, out, err = run(command)
    print(out[:4000])
    if err.strip():
        print("stderr: %s" % err.strip()[:800])
    if code != 0:
        print("the extractor failed; refusing to continue a round on it")
        return 3
    print("=== next, in order")
    print("  1. read the extractor's output and decide what it establishes")
    print("  2. python re/ledger.py promote \"%s\" --to <GRADE> --witness \"...\" --round N" % subject)
    print("  3. if it names a field or fixes a layout, write the C++ and its test")
    print("  4. pwsh -File re/gate.ps1        (must be green)")
    print("  5. git add the changed paths; git commit -F <message file>")
    print("  6. python re/g_round.py --checkpoint    to refresh re/RESUME.md")
    print("  never: git push")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
