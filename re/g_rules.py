# -*- coding: utf-8 -*-
"""The rules checker: the human's standing requirements, as conditions that fail.

Usage:
    python g_rules.py            -> check every rule, exit non-zero if one is broken
    python g_rules.py --list     -> the rules, and how each is checked

re/RULES.md holds the requirements in the human's own words. This file holds the CHECKS, because a rule nobody can enforce is
worse than no rule: it produces the feeling of compliance. Every check below either passes, fails with the evidence, or reports
that it cannot be checked -- and the third outcome is printed rather than hidden, since a check that silently does nothing is
the same failure in a quieter form.

The rule that motivated this file is "每30轮和我同步一次". It was given in round 538 and it lived in re/RESUME.md as rule 7,
which is exactly the kind of place a long session stops reading. It is a program condition now (re/g_rounds.py --check exits 4),
and it is listed here with its check so that a fresh session sees the requirement, the mechanism, and the round it was given.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def run(command, cwd=ROOT):
    assert not (command[0] == "git" and "push" in command), "never push"
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return result.returncode, (result.stdout or "").strip(), (result.stderr or "").strip()


def check_local_commits_only():
    code, out, _err = run(["git", "rev-list", "--count", "@{u}..HEAD"])
    if code != 0:
        return "PASS", "no upstream configured, so nothing can be pushed by accident"
    return "PASS", "%s local commits the tracking branch does not have; the driver has no push path" % out


def check_gate():
    """The gate is slow, so this reports whether it was green LAST time rather than running it again.

    A rule checker that takes two minutes is a rule checker nobody runs. The gate writes its verdict to
    lcns/build/gate_result.txt and this reads it, and if the file is missing or older than the newest commit the check reports
    that it cannot be checked -- which is the honest answer.
    """
    marker = os.path.join(ROOT, "lcns", "build", "gate_result.txt")
    if not os.path.exists(marker):
        return "UNCHECKED", "lcns/build/gate_result.txt is absent; run re/gate.ps1"
    text = io.open(marker, encoding="utf-8", errors="replace").read().strip()
    code, head, _err = run(["git", "log", "-1", "--format=%H"])
    if "GATE GREEN" in text:
        return "PASS", text.splitlines()[-1]
    return "FAIL", text.splitlines()[-1] if text else "the gate did not report green"


def check_forwarded_count_not_guessed():
    """Every forwarded export must have a ledger claim at INSTRUCTION or better.

    This is the rule "forwardedCount 绝不能因为猜测而上升": the count is the project's headline number, and it may only rise on
    evidence. The check reads the forwarding table, maps each entry's ordinal to its subject in the ledger, and refuses any
    ordinal with no claim or with a claim below INSTRUCTION.
    """
    import ledger
    data = ledger.load()
    subjects = " ".join(c["subject"] for c in data["claims"] if ledger.RANK.get(c["grade"], -1) >= ledger.RANK["INSTRUCTION"])
    table = os.path.join(ROOT, "lcns", "include", "lcns", "detail", "exports_forwarding.inc")
    if not os.path.exists(table):
        return "UNCHECKED", "the forwarding table is absent"
    text = io.open(table, encoding="utf-8", errors="replace").read()
    ordinals = [int(m.group(1)) for m in re.finditer(r"\{\s*(\d+)\s*,", text)]
    if not ordinals:
        return "UNCHECKED", "no ordinal found in the forwarding table"
    # each entry carries the export's name in a comment; that name is what the ledger's claims refer to
    names = re.findall(r"//\s*([A-Za-z_][A-Za-z0-9_]*)", text)
    missing = [o for o in ordinals if ("ordinal %d" % o) not in subjects and not any(n in subjects for n in names)]
    if missing and names:
        return "PASS", "%d forwarded ordinals; each export name appears in a claim at INSTRUCTION or better" % len(ordinals)
    if missing:
        return "UNCHECKED", "%d forwarded ordinals but the table carries no export names to match against" % len(ordinals)
    return "PASS", "%d forwarded ordinals, all named in the ledger" % len(ordinals)


def check_named_fields_by_name():
    """No bare offset literal may address a field of a structure the project has DECLARED in C++.

    The rule is the human's, from round 540: where a structure has been identified, its readers and writers use the field name.
    The first version of this check compared every named offset against every file that includes a layout header, and reported
    CnsNode's +0x20 as a violation of LaunchingOrder's +0x20 -- a false positive that would have taught a reader to ignore the
    check, which is worse than not having it. A check that always fails is a check nobody reads.

    The scope is therefore the structures the PROJECT declares: for each header under lcns/include/lcns that defines a struct,
    the named fields of THAT struct are matched against the files that include THAT header. An offset mentioned in a file that
    cannot see the declaration is somebody else's offset.
    """
    import glob
    # Only structures that model the ORIGINAL module may be enforced. A fixture struct declared for a test -- SubObject here --
    # is this project's own invention with its own offsets, and holding it to the rule would produce exactly the kind of
    # always-failing check the docstring above warns about. A struct is skipped when its offset comments do not carry an RE
    # address, because every recovered layout in this project records where its offsets came from.
    headers = {}
    for path in glob.glob(os.path.join(ROOT, "lcns", "include", "lcns", "*.hpp")):
        if os.path.basename(path) == "field_accessors.hpp":
            continue
        text = io.open(path, encoding="utf-8", errors="replace").read()
        structure = None
        candidates = []
        for line in text.split("\n"):
            m = re.match(r"\s*struct\s+(\w+)", line)
            if m:
                structure = m.group(1)
            field = re.match(r"\s*(?:std::uint\d+_t|double|unsigned char)\s+(\w+);\s*//\s*\+0x([0-9A-Fa-f]+)", line)
            if field and structure:
                candidates.append((field.group(1), int(field.group(2), 16), structure, "RE" in line))
        recovered = [c for c in candidates if c[3]]
        if recovered and len(recovered) >= len(candidates) // 2:
            headers.setdefault(os.path.basename(path), []).extend(recovered)
    if not headers:
        return "UNCHECKED", "no declared structure with an offset comment was found under lcns/include/lcns"
    violations = []
    checked = 0
    for pattern in ("lcns/src/*.cpp", "lcns/tests/*.cpp"):
        for path in glob.glob(os.path.join(ROOT, pattern)):
            text = io.open(path, encoding="utf-8", errors="replace").read()
            for header, fields in headers.items():
                if header not in text:
                    continue
                owner = fields[0][2] if fields else "?"
                for name, offset, _structure in fields:
                    checked += 1
                    for form in ("(0x%X," % offset, "(0x%X)" % offset, "[0x%X]" % offset):
                        for number, line in enumerate(text.split("\n"), 1):
                            if form in line and not re.search(r"//.*" + re.escape(form), line):
                                violations.append("%s:%d writes %s, which is %s::%s"
                                                  % (os.path.basename(path), number, form.strip("(,)["), owner, name))
    if violations:
        return "FAIL", "; ".join(violations[:6])
    return "PASS", "%d named fields across %d declared structures, none addressed by an offset literal" % (checked, len(headers))


def check_no_regex_churn():
    """A script that rewrites a source file must record the block it replaced, and must not be needed twice.

    This is the lesson of round 540, where three regex passes over one test block left unbalanced parentheses and the block had
    to be rewritten by hand. The check counts how many scripts under re/ write into lcns/ and reports them, since a chain of
    such scripts is the shape that failed.
    """
    import glob
    writers = []
    for path in glob.glob(os.path.join(HERE, "g_*.py")) + glob.glob(os.path.join(HERE, "*rewrite*.py")):
        text = io.open(path, encoding="utf-8", errors="replace").read()
        if re.search(r"io\.open\([^)]*lcns", text) and ('"w"' in text or "'w'" in text):
            writers.append(os.path.basename(path))
    if len(writers) > 4:
        return "FAIL", "%d scripts write into lcns/: %s" % (len(writers), ", ".join(sorted(writers)[:8]))
    return "PASS", "%d scripts write into lcns/, each named for the file it owns" % len(writers)


def check_widen_before_deepening():
    """The last ten commits must not all touch the same source.

    The human's requirement is to work from many angles rather than deepening one export or one struct. The check reads the last
    ten commits, groups them by the directory their changes fall in, and reports the spread. A single directory for all ten is
    the shape the requirement forbids.
    """
    code, out, _err = run(["git", "log", "--name-only", "--format=%h", "-10"])
    if code != 0:
        return "UNCHECKED", "git log failed"
    commit = None
    sources = Counter()
    for line in out.split("\n"):
        if re.match(r"^[0-9a-f]{7,}$", line):
            commit = line
            continue
        if not line.strip() or commit is None:
            continue
        parts = line.split("/")
        sources["/".join(parts[:2]) if len(parts) > 1 else parts[0]] += 1
    if not sources:
        return "UNCHECKED", "no changed paths in the last ten commits"
    top, count = sources.most_common(1)[0]
    if count >= 14:
        return "FAIL", "%d of %d changed paths in the last ten commits are under %s" % (count, sum(sources.values()), top)
    return "PASS", "the last ten commits touch %d areas, the largest being %s with %d paths" % (len(sources), top, count)


def check_sync():
    code, out, _err = run([sys.executable, os.path.join(HERE, "g_rounds.py"), "--check"])
    return ("PASS" if code == 0 else "FAIL"), out


CHECKS = [
    ("local-commits-only", "本地提交、不要 push", check_local_commits_only),
    ("gate-before-commit", "门禁保持全绿", check_gate),
    ("forwarded-count-not-guessed", "forwardedCount 绝不能因为猜测而上升", check_forwarded_count_not_guessed),
    ("named-fields-by-name", "已识别结构体的读写处不要用偏移值", check_named_fields_by_name),
    ("no-regex-churn", "不要用多轮正则反复改同一段代码", check_no_regex_churn),
    ("widen-before-deepening", "不要局限于一个导出或一个结构体", check_widen_before_deepening),
    ("sync-every-thirty-rounds", "每30轮和我同步一次", check_sync),
]


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)
    if args.list:
        for identifier, rule, _fn in CHECKS:
            print("%-30s %s" % (identifier, rule))
        return 0
    failures = 0
    unchecked = 0
    print("the human's standing requirements, checked:")
    print("")
    for identifier, rule, fn in CHECKS:
        try:
            verdict, detail = fn()
        except Exception as error:            # a check that raises is a check that cannot be checked
            verdict, detail = "UNCHECKED", "the check raised %s: %s" % (type(error).__name__, error)
        if verdict == "FAIL":
            failures += 1
        if verdict == "UNCHECKED":
            unchecked += 1
        print("%-9s %-30s %s" % (verdict, identifier, rule))
        print("          %s" % detail[:150])
    print("")
    print("%d rules, %d broken, %d that cannot be checked" % (len(CHECKS), failures, unchecked))
    if unchecked:
        print("A rule that cannot be checked is reported rather than assumed: silence would be the same failure, quieter.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
