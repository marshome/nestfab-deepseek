"""One-off namespace migration: move the DLL access layer into lcns::dll."""
import io
import os
import re

ROOT = r"D:\Nesting\nestfab\lcns"

# --- model.hpp: include the shared enums header instead of api.hpp ---
p = os.path.join(ROOT, "include", "lcns", "model.hpp")
s = io.open(p, encoding="utf-8").read()
s = s.replace('#include "lcns/api.hpp"   // Objective / NestingOrigin',
              '#include "lcns/enums.hpp"   // Objective / NestingOrigin (recovered enums)')
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("model.hpp patched")

# --- api.cpp: wrap the implementation in namespace lcns::dll ---
p = os.path.join(ROOT, "src", "api.cpp")
s = io.open(p, encoding="utf-8").read()
s = s.replace("namespace lcns {\nnamespace {", "namespace lcns {\nnamespace dll {\nnamespace {", 1)
assert s.rstrip().endswith("}  // namespace lcns")
s = s.rstrip()[: -len("}  // namespace lcns")] + "}  // namespace dll\n}  // namespace lcns\n"
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("api.cpp patched")

# --- probe app: qualify the moved names ---
p = os.path.join(ROOT, "apps", "probe", "main.cpp")
s = io.open(p, encoding="utf-8").read()
s = re.sub(
    r"\blcns::(Diagnostic|diagnoseFile|exportCount|exportTable|Confidence|formatExportTable|Library|Api)\b",
    r"lcns::dll::\1",
    s,
)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("probe patched")

# --- tests: test_nofit / test_nester use only model+engine, test_model uses enums ---
# nothing to do, they reference lcns::Objective / lcns::NestingOrigin / lcns::Confidence
print("done")
