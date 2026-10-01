# -*- coding: utf-8 -*-
"""Write the commit message to a file (no BOM, exact quotes) and commit it."""
import io
import subprocess

MSG = u"""recovery.hpp: carry the Chinese meaning of every status macro in the code itself

The five marks now spell out what they mean: in the macro block, in the Status
enum, in recovery::toChinese(), and inside the static_assert message. So the
meaning is greppable in the code, not only in the docs:

    grep -rn "LCNS_NOT_REVERSED" src include   # by macro name
    grep -rn "\u5c1a\u672a\u9006\u5411"          src include   # by meaning

Strictly speaking LCNS_NOT_REVERSED is the only mark that means "not reverse
engineered yet" (11 entries). LCNS_SUBSTITUTED (27) is where the un-reversed
*behaviour* lives -- 15 of those are the strategy Run bodies plus the main
packer, which is why the nesting density is still far below the literature.

tests/test_recovered.cpp asserts the Chinese word table (toChinese), so the
wording cannot drift away from the code marks.

Also refreshed the stale README figures (58 -> 60 entries, 6/13/26/12/1 ->
7/14/27/11/1) and removed the now wrong "COIN-OR Clp" example of a substitute:
the real Clp 1.15.3 is linked in as of the previous commit.
"""

path = r"D:\Nesting\nestfab\.git\COMMIT_MSG_TMP"
io.open(path, "w", encoding="utf-8", newline="\n").write(MSG)
print(subprocess.run(["git", "-C", r"D:\Nesting\nestfab", "commit", "-F", path],
                     capture_output=True, text=True).stdout.strip()[:400])
