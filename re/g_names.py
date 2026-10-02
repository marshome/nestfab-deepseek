# -*- coding: utf-8 -*-
"""One place to ask what a function is called.

    python g_names.py            -> the summary
    python g_names.py 0x1DD50    -> the entry for one address

The names come from re/name_registry.json, which re/g_harvest_names.py fills from the call sites of the module's reporter
channels. Two kinds are in there and they are NEVER mixed:

  * a name read from the function's OWN call site -- the module naming itself in an assertion or a log line, which is
    evidence;
  * a guess taken from a function it calls, which is a hypothesis.

`direct()` returns only the first kind, and that is what the worklist tools use, so an address in a closure listing is
labelled with a name only when the module itself supplied it.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, "name_registry.json")

_registry = None


def _load():
    global _registry
    if _registry is None:
        try:
            _registry = json.load(io.open(REGISTRY, encoding="utf-8"))
        except Exception:
            _registry = {}
    return _registry


def entry(addr):
    return _load().get("0x%X" % addr) or {}


def direct(addr):
    """The name the module gives this function itself, or None. Never a guess."""
    value = entry(addr)
    own = [v for v in (value.get("via") or []) if not v.startswith("via ")]
    if value.get("methods") and own:
        return value["methods"][0]
    return None


def channel(addr):
    value = entry(addr)
    own = [v for v in (value.get("via") or []) if not v.startswith("via ")]
    return ",".join(own) if own else None


def guessed(addr):
    """A name taken from a function this one calls. A hypothesis, and labelled as one."""
    value = entry(addr)
    return (value.get("guessed_from_callees") or [None])[0]


def label(addr):
    """What to print next to an address in a listing."""
    name = direct(addr)
    if name:
        return name
    guess = guessed(addr)
    if guess:
        return guess + "?"
    return None


def main(argv):
    if argv and argv[0].startswith("0x"):
        addr = int(argv[0], 16)
        print(json.dumps(entry(addr), indent=1, sort_keys=True))
        return 0
    reg = _load()
    named = [k for k, v in reg.items() if v.get("methods") and any(not s.startswith("via ") for s in (v.get("via") or []))]
    guessed_only = [k for k, v in reg.items() if not v.get("methods") and v.get("guessed_from_callees")]
    print("re/name_registry.json: %d entries" % len(reg))
    print("  named from their own call site: %d" % len(named))
    print("  with only a guessed name      : %d" % len(guessed_only))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
