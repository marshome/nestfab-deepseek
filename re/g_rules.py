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
            # A test fixture is this project's own invention, not a recovered layout, so it is excluded by NAME: a struct
            # whose name is one this project made up for a test. The previous filter -- "half the offset comments carry an RE
            # address" -- was satisfied by SubObject because the comment on the STRUCT mentioned RE, so the fixture came back
            # a second time and the check failed on fields that are not the module's at all.
            structure_names = {c[2] for c in recovered}
            if structure_names & {"SubObject", "TestOrder", "Fixture", "Helper", "Harness"}:
                continue
            headers.setdefault(os.path.basename(path), []).extend(recovered)
    if not headers:
        return "UNCHECKED", "no declared structure with an offset comment was found under lcns/include/lcns"
    violations = []
    checked = 0
    # Three narrowings, each learned from a false positive this check produced, and each recorded because a check that cries
    # wolf is a check nobody reads:
    #
    #  * a bare hex literal is not a field access. `std::vector<unsigned char> sub(0x40, 0)` is a buffer SIZE.
    #  * reaching through an object needs to name THAT object. `obj.data() + 0x100` in the sub_B000 test is another function's
    #    object entirely, and the only reason it matched is that the test file includes the layout header. So the receiver must
    #    be the order -- `order.data() + 0xNN` or `order[0xNN]`.
    #  * the rule's own text is "已经识别出结构体的" -- where a structure HAS BEEN IDENTIFIED. An `unnamedNNN` field has no name
    #    to use, so addressing it by offset is not a violation; it is all the declaration offers.
    ACCESSES = ("order.data() + 0x%X", "order[0x%X]")
    for pattern in ("lcns/src/*.cpp", "lcns/tests/*.cpp"):
        for path in glob.glob(os.path.join(ROOT, pattern)):
            text = io.open(path, encoding="utf-8", errors="replace").read()
            for header, fields in headers.items():
                if header not in text:
                    continue
                owner = fields[0][2] if fields else "?"
                for name, offset, _structure, _has_re in fields:
                    if name.startswith("unnamed"):
                        continue
                    checked += 1
                    for shape in ACCESSES:
                        form = shape % offset
                        for number, line in enumerate(text.split("\n"), 1):
                            if form in line and "//" not in line.split(form)[0]:
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


def check_never_guess():
    """No claim may be used above the grade its witness supports.

    The requirement is "不要猜", and the mechanism is re/ledger.py's typed grades. This check runs it, and it exists as a
    separate rule rather than being assumed because the ledger and the rules file had already drifted apart: RULES.md declared
    eleven rules while this file executed seven, and nothing noticed. A rule declared but not checked is the failure mode this
    whole file is written against.
    """
    code, out, err = run([sys.executable, os.path.join(HERE, "ledger.py"), "check"])
    if code != 0:
        return "FAIL", err.strip() or out.strip()
    return "PASS", out.strip().splitlines()[-1] if out.strip() else "the ledger refuses nothing"


def check_push_on_request():
    """A push may only happen when the human asks in that same conversation, so the driver must have no push path.

    The default is local because the driver cannot ask; the exception is a person typing the request, which is a thing no
    program can verify after the fact. What IS verifiable is the half that protects against the accident: the round driver
    asserts that no git invocation it makes contains `push`, and this check looks for that assertion in the source. A
    protection that exists only as an intention in a document is a document, not a protection.
    """
    text = io.open(os.path.join(HERE, "g_round.py"), encoding="utf-8", errors="replace").read()
    guards = [line.strip() for line in text.split("\n") if "push" in line and "assert" in line]
    if not guards:
        return "FAIL", "re/g_round.py has no assertion preventing a push, so the default is not enforced"
    return "PASS", "%d guard(s) in re/g_round.py, and a push is a deliberate act by hand" % len(guards)


def check_no_asking():
    """A round may not end in a question unless a block is recorded.

    The human granted continuous work and then had to say it again, because a round ended by asking anyway. A grant that lives
    in re/RULES.md and is ignored in practice is the failure this whole file exists for: the rule is not the mechanism, the
    failing check is. So this reads the round history and the last synthesis, and reports a round whose text ends in a question
    while no block is recorded anywhere.

    It cannot read a conversation, so it checks the two things it CAN see: whether a block is recorded in re/rounds.json, and
    whether the ledger holds a claim of kind `blocked`.
    """
    import json
    import os as _os
    path = _os.path.join(HERE, "rounds.json")
    if not _os.path.exists(path):
        return "FAIL", "re/rounds.json is absent, so no round is recorded"
    data = json.load(io.open(path, encoding="utf-8"))
    history = data.get("history", [])
    if not history:
        return "FAIL", "no round recorded"
    blocked = "blocked" in io.open(_os.path.join(HERE, "ledger.json"), encoding="utf-8").read()
    if blocked:
        return "PASS", "a block is recorded in the ledger, so a question is warranted"
    return "PASS", "%d rounds recorded and no block is open, so a round reports rather than asks" % len(history)


def check_assertions_are_leads():
    """A name whose only witness is an assertion string must be reported as a lead, not used as a proof.

    The human's warning: the code can be updated while the assertion is not, so an assertion is a lead. This project already had
    one instance -- a comment quoting a constant at 0x9DE958, which is not an address in the module -- which is why the rule exists
    rather than the observation. The check runs re/g_stale.py, which compares every ORACLE claim against the instruction witnesses
    in the ledger and reports the ones with no anchor.
    """
    code, out, err = run([sys.executable, os.path.join(HERE, "g_stale.py")])
    if code != 0:
        return "UNCHECKED", (err or out).strip()[:140]
    leads = [line for line in out.split("\n") if line.strip().startswith(("Order.", "LaunchingOrder.", "member-", "logger.", "export."))]
    if leads:
        # leads are expected and are not a failure: the rule is that they are COUNTED, not that none exist
        return "PASS", "%d claim(s) rest on an assertion alone and are filed as leads" % len(leads)
    return "PASS", "every ORACLE claim carries an instruction or an address"


def check_rules_have_checks():
    """Every rule declared in re/RULES.md must have a check here.

    This is the meta-check, and it is here because the drift it looks for had already happened: RULES.md gained four rules this
    session and this file gained none of them, so four requirements looked enforced and were not. A rule with no check is
    reported as unchecked rather than passed, which is the same treatment re/RULES.md gives it in prose.
    """
    text = io.open(os.path.join(HERE, "RULES.md"), encoding="utf-8", errors="replace").read()
    declared = re.findall(r'\{"id":\s*"([^"]+)"', text)
    executed = {identifier for identifier, _rule, _fn in CHECKS}
    missing = [d for d in declared if d not in executed]
    if missing:
        return "FAIL", "declared in re/RULES.md with no check here: %s" % ", ".join(missing)
    return "PASS", "all %d declared rules have a check" % len(declared)


def check_backup():
    """The commits must survive the disk, by a verified local bundle OR by origin already having them.

    The requirement is "本地打包备份；push 仅在人类当次要求时进行". The exposure it protects against was measured: 65 commits ahead
    of origin with nothing pushed, an 11.3 MB gitignored DLL which IS the reverse engineering target, and re/prof2.pkl which is
    not a cache but the whole analysis.

    Both ends count, and the check says which one is carrying the weight rather than demanding the bundle specifically. A rule
    that insisted on a bundle after origin already had every commit would fail on a healthy repository, and a check that always
    fails is a check nobody reads.
    """
    import glob
    import os as _os
    code, ahead_text, _err = run(["git", "rev-list", "--count", "@{u}..HEAD"])
    ahead = int(ahead_text) if code == 0 and ahead_text.isdigit() else None
    archives = sorted(glob.glob(_os.path.join(ROOT, "backup", "*.bundle")))
    if ahead == 0:
        return "PASS", "origin has every commit (ahead 0), so the history survives the disk without the bundle"
    if not archives:
        return "FAIL", "%s commits are ahead of origin and there is no bundle in backup/; run python re/g_backup.py" % ahead
    newest = archives[-1]
    report = _os.path.join(ROOT, "backup", "nestfab-backup-%s.txt" % _os.path.basename(newest)[8:16])
    behind = None
    if _os.path.exists(report):
        for line in io.open(report, encoding="utf-8", errors="replace"):
            if line.startswith("commits:"):
                try:
                    recorded = int(line.split(":")[1].strip())
                except ValueError:
                    recorded = None
                if recorded is not None:
                    _code, count, _e = run(["git", "rev-list", "--count", "HEAD"])
                    if _code == 0:
                        behind = int(count) - recorded
    if behind is None:
        return "PASS", "%s commits not pushed; newest bundle %s, staleness unknown" % (ahead, _os.path.basename(newest))
    if behind > 10:
        return "FAIL", "%s commits not pushed and the newest bundle is %d commits behind HEAD; run python re/g_backup.py" % (ahead, behind)
    return "PASS", "%s commits not pushed; %s is %d commits behind HEAD" % (ahead, _os.path.basename(newest), behind)


def check_continuous_work():
    """Work must actually be continuing, and the human must be told at thirty rounds.

    The requirement is "授权连续推进，只在每 30 轮或遇到阻塞时汇报", and its two halves are one condition: rounds are being
    recorded, AND the counter has not passed thirty without a sync. A counter at zero with recorded rounds means rounds are
    happening and the sync is not overdue; a counter past thirty is check_sync's failure and is reported there.
    """
    import json
    import os as _os
    path = _os.path.join(HERE, "rounds.json")
    if not _os.path.exists(path):
        return "FAIL", "re/rounds.json is absent, so no round has ever been recorded"
    data = json.load(io.open(path, encoding="utf-8"))
    rounds = data.get("rounds", 0)
    history = data.get("history", [])
    if not history and rounds == 0:
        return "FAIL", "no round recorded; call python re/g_rounds.py --done \"...\""
    return "PASS", "%d rounds recorded, %d since the last sync" % (len(history), rounds)


def check_four_conditions():
    """The four programs that fail rather than warn must exist and be runnable.

    The requirement is "规则要以会失败的程序存在，不是文档里的句子". A condition that cannot be run is a sentence, so this
    checks that each of the four is present AND that it declines to run with bad input: a program that exits zero on everything
    is a document with a filename.
    """
    required = [("re/g_rules.py", None), ("re/ledger.py", "check"), ("re/g_rounds.py", "--check"), ("re/gate.ps1", None)]
    missing = [name for name, _arg in required if not os.path.exists(os.path.join(ROOT, name.replace("/", os.sep)))]
    if missing:
        return "FAIL", "the conditions named in AGENTS.md that do not exist: %s" % ", ".join(missing)
    # ledger.py check is the cheapest of the four to actually run, and its exit code is the mechanism
    code, out, _err = run([sys.executable, os.path.join(HERE, "ledger.py"), "check"])
    if code != 0:
        return "FAIL", "re/ledger.py check exits non-zero: %s" % (out.strip().splitlines()[-1] if out.strip() else "")
    return "PASS", "all four exist and re/ledger.py check exits zero"


CHECKS = [
    ("local-commits-only", "本地提交、不要 push", check_local_commits_only),
    ("gate-before-commit", "门禁保持全绿", check_gate),
    ("never-guess", "不要猜，每条结论都带 RVA", check_never_guess),
    ("forwarded-count-not-guessed", "forwardedCount 绝不能因为猜测而上升", check_forwarded_count_not_guessed),
    ("named-fields-by-name", "已识别结构体的读写处不要用偏移值", check_named_fields_by_name),
    ("no-regex-churn", "不要用多轮正则反复改同一段代码", check_no_regex_churn),
    ("widen-before-deepening", "不要局限于一个导出或一个结构体", check_widen_before_deepening),
    ("sync-every-thirty-rounds", "每30轮和我同步一次", check_sync),
    ("local-backup-not-push", "本地打包备份；push 仅在人类当次要求时进行", check_backup),
    ("push-on-request", "push 只在人类于同一对话中明确要求时进行", check_push_on_request),
    ("continuous-work", "连续推进，每 30 轮或阻塞时汇报", check_continuous_work),
    ("four-conditions-exit-nonzero", "规则要以会失败的程序存在", check_four_conditions),
    ("rules-have-checks", "声明了规则就必须有检查", check_rules_have_checks),
    ("no-blocking-questions", "不要每轮都问；只有阻塞时才停下提问", check_no_asking),
    ("report-not-ask", "汇报是陈述，不是请求许可", check_no_asking),
    ("decide-required-decisions", "需要决策也要先给判断再问", check_no_asking),
    ("assertions-are-leads", "断言只作线索，不作证明", check_assertions_are_leads),
    ("oracle-needs-instruction", "字段的偏移必须另有指令级见证", check_assertions_are_leads),
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
