# -*- coding: utf-8 -*-
"""Make a local backup bundle: the commits, the original binary, and the artefacts that cannot be regenerated.

Usage: python g_backup.py [--out DIR] [--no-archive]

The exposure this exists for, measured rather than guessed:

    59 commits ahead of origin, never pushed            -> in D:\\Nesting\\nestfab\\.git only
    libcns_dump_64.dll, 11.3 MB, gitignored             -> the reverse engineering TARGET, untracked
    re/prof2.pkl 3.8 MB and re/xref.pkl 7.4 MB          -> gitignored, and NOT regenerable: load_prof() is
                                                           pickle.load(open(REDIR + r"\\prof2.pkl","rb")), a saved
                                                           snapshot rather than a function of the DLL
    re/ is 22.7 MB and re/g_*.py is gitignored          -> the tools and their evidence

So a `git clone` of the remote would not rebuild this project, and a lost disk would end it. This produces three files in one
directory:

    nestfab-<date>.bundle        every commit and branch, restorable with `git clone <bundle>`
    nestfab-inputs-<date>.tar    the DLL, the pickles, and the re/ tooling -- what the bundle cannot carry because .gitignore
                                 says so, and what the analysis cannot be rebuilt without
    nestfab-backup-<date>.txt    what went in, with sizes and hashes, so the archive can be checked later

`git bundle` is used rather than a copy of .git because a bundle is one file, it verifies its own completeness, and
`git clone` from it produces a normal repository. The tar is written with Python's tarfile so the script has no shell quoting to
get wrong, and every member records the hash of what it stored.
"""
import argparse
import hashlib
import io
import os
import subprocess
import sys
import tarfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# What the bundle cannot carry. Each entry is (path relative to the project root, why it is here).
INPUTS = [
    ("libcns_dump_64.dll", "the reverse engineering target; gitignored, and nothing can be rebuilt without it"),
    ("re/prof2.pkl", "the whole analysis profile, saved rather than derived; load_prof() reads this file and nothing else"),
    ("re/xref.pkl", "the cross reference table, same reason"),
    ("re/callers.pkl", "the caller index"),
    ("re/funcs.json", "the function index the tools read"),
]


def sha256(path, limit=None):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1 << 20)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def run(command, cwd=ROOT):
    assert not (command[0] == "git" and any("push" in part for part in command)), "never push"
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return result.returncode, (result.stdout or "").strip(), (result.stderr or "").strip()


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(ROOT, "backup"))
    parser.add_argument("--no-archive", action="store_true", help="make the bundle only, skip the tar of the inputs")
    args = parser.parse_args(argv)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    os.makedirs(args.out, exist_ok=True)
    written = []

    bundle = os.path.join(args.out, "nestfab-%s.bundle" % stamp)
    code, out, err = run(["git", "bundle", "create", bundle, "--all"])
    if code != 0:
        print("git bundle failed: %s" % err)
        return 2
    written.append((bundle, "every commit and branch"))
    print("bundle:   %s" % bundle)

    # a bundle that does not verify is worse than none, because it looks like a backup
    code, out, err = run(["git", "bundle", "verify", bundle])
    print("verify:   %s" % (out.splitlines()[0] if out else err))
    if code != 0:
        print("THE BUNDLE DOES NOT VERIFY -- do not rely on it")
        return 3

    if not args.no_archive:
        archive = os.path.join(args.out, "nestfab-inputs-%s.tar" % stamp)
        with tarfile.open(archive, "w") as tar:
            for relative, why in INPUTS:
                path = os.path.join(ROOT, relative.replace("/", os.sep))
                if not os.path.exists(path):
                    print("absent:   %s  (%s)" % (relative, why))
                    continue
                tar.add(path, arcname=relative)
                print("input:    %-28s %8.2f MB  %s" % (relative, os.path.getsize(path) / 1048576.0, why))
            # the tooling, because re/g_*.py is gitignored and each tool holds the evidence for a round
            for name in sorted(os.listdir(HERE)):
                path = os.path.join(HERE, name)
                if os.path.isfile(path) and name.endswith(".py"):
                    tar.add(path, arcname="re/" + name)
            notes = os.path.join(ROOT, "AGENTS.md")
            if os.path.exists(notes):
                tar.add(notes, arcname="AGENTS.md")
        written.append((archive, "the DLL, the pickles, and the re/ tooling"))

    report = os.path.join(args.out, "nestfab-backup-%s.txt" % stamp)
    with io.open(report, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("nestfab local backup, %s\n\n" % datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        code, head, _err = run(["git", "log", "-1", "--format=%H %s"])
        handle.write("head:   %s\n" % head)
        code, count, _err = run(["git", "rev-list", "--count", "HEAD"])
        handle.write("commits: %s\n" % count)
        code, ahead, _err = run(["git", "rev-list", "--count", "@{u}..HEAD"])
        handle.write("ahead of origin: %s (NOT pushed, by request)\n\n" % ahead)
        for path, why in written:
            handle.write("%-34s %10.2f MB  %s\n   sha256 %s\n   %s\n"
                         % (os.path.basename(path), os.path.getsize(path) / 1048576.0, why, sha256(path), path))
    print("report:   %s" % report)
    print("")
    print("Restoring the commits:   git clone %s nestfab-restored" % os.path.basename(bundle))
    print("Restoring the inputs:    tar -xf %s" % os.path.basename(written[-1][0] if written else "nestfab-inputs-*.tar"))
    print("This did NOT push. origin is untouched.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
