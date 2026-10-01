# -*- coding: utf-8 -*-
"""Fetch the third party libraries libcns_dump_64.dll was linked against.

Rationale (human instruction, goal round 2): a third party library must be DOWNLOADED AND LINKED,
not reverse engineered. The manifest below is evidence based -- every entry cites the string in the
dump that proves the library is used, and the version where the dump states one.

Run:  python third_party/fetch.py [--only boost,clp,...] [--list]
"""
import argparse
import hashlib
import io
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.join(HERE, "_archives")

# name, version, url, licence, evidence in the dump, purpose in lcns
MANIFEST = [
    dict(name="boost", version="1.63.0",
         url="https://archives.boost.io/release/1.63.0/source/boost_1_63_0.tar.bz2",
         licence="Boost Software License 1.0",
         evidence=r"0x9AE7A0 'C:\Users\renaud\nest\external\boost_1_63_0/boost/uuid/sha1.hpp'; "
                  r"also boost/multiprecision/rational_adaptor.hpp (0x592870)",
         purpose="exact arithmetic (multiprecision) + sha1/uuid in the licence and cloud paths"),
    dict(name="CoinUtils", version="2.11.12",
         url="https://github.com/coin-or/CoinUtils/archive/refs/tags/releases/2.11.12.tar.gz",
         licence="EPL-2.0",
         evidence="OsiClpSolverInterface / clpModel->... strings at 0x9C31A3 ff.",
         purpose="COIN-OR base (CoinUtils): required by Osi and Clp"),
    dict(name="Osi", version="0.108.11",
         url="https://github.com/coin-or/Osi/archive/refs/tags/releases/0.108.11.tar.gz",
         licence="EPL-2.0",
         evidence="0x9C31FC 'OsiSolverInterface'; OsiHintDo / OsiForceDo / OsiColCut",
         purpose="the solver interface layer the binary drives the LP through"),
    dict(name="Clp", version="1.17.10",
         url="https://github.com/coin-or/Clp/archive/refs/tags/releases/1.17.10.tar.gz",
         licence="EPL-2.0",
         evidence="'clp' + 'ClpSolve' at 0x9C2E40/0x3716DC; clpModel->setSpecialOptions(...) "
                  "assertion text",
         purpose="THE LP solver the original statically links; replaces lcns's hand written Simplex"),
    dict(name="jsoncpp", version="1.9.5",
         url="https://github.com/open-source-parsers/jsoncpp/archive/refs/tags/1.9.5.tar.gz",
         licence="MIT",
         evidence="the JsonCpp key/value strings and the writer/reader shape used by "
                  "saveProblem/loadProblem",
         purpose="the JSON serialisation the original uses for problems and solutions"),
    dict(name="cryptopp", version="8.9.0",
         url="https://github.com/weidai11/cryptopp/archive/refs/tags/CRYPTOPP_8_9_0.tar.gz",
         licence="Boost Software License 1.0 (public domain parts)",
         evidence="0x9B8C98 'CryptoPP: invalid group element'; vtable N8CryptoPP10HexEncoderE etc.",
         purpose="hashes/encryption in the licensing and cloud paths"),
]


def human(n):
    return "%.1f MB" % (n / 1048576.0) if n else "?"


def fetch(entry, force=False):
    os.makedirs(ARCH, exist_ok=True)
    dest = os.path.join(ARCH, os.path.basename(entry["url"]))
    if os.path.exists(dest) and not force:
        print("   %-10s already present (%s)" % (entry["name"], human(os.path.getsize(dest))))
        return dest
    print("   %-10s GET %s" % (entry["name"], entry["url"]))
    req = urllib.request.Request(entry["url"], headers={"User-Agent": "lcns-re/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, io.open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        got = 0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
            if total:
                sys.stdout.write("\r      %s / %s" % (human(got), human(total)))
                sys.stdout.flush()
    print("\r      got %s%s" % (human(os.path.getsize(dest)), " " * 20))
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.list:
        for e in MANIFEST:
            print("%-10s %-9s %-46s %s" % (e["name"], e["version"], e["licence"], e["purpose"]))
        return
    only = {s.strip().lower() for s in a.only.split(",") if s.strip()}
    for e in MANIFEST:
        if only and e["name"].lower() not in only:
            continue
        try:
            p = fetch(e, a.force)
            h = hashlib.sha256(io.open(p, "rb").read()).hexdigest()[:16]
            print("      sha256[:16]=%s" % h)
        except Exception as ex:
            print("   %-10s FAILED: %s" % (e["name"], ex))
    print("archives in", ARCH)


if __name__ == "__main__":
    main()
