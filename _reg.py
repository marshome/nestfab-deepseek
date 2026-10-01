import io, re, subprocess
RP = r"D:\Nesting\nestfab\lcns\include\lcns\recovery.hpp"
r = io.open(RP, encoding="utf-8", newline="").read().replace("\r\n","\n")
r = re.sub(r'    \{"verify\.defect_reduction".*?\},\n', '', r, flags=re.S)
A = u'    {"tu.equivalent", Status::NotReversed,'
assert A in r, "anchor"
ENT = (u'    {"verify.defect_reduction", Status::Structural, "0x4BC9E0 (reduction form), 0x4F9C30 (getter)",\n'
       u'     "the equivalent-problem defect reduction. RECOVERED at instruction level: the form is '
       u'x - 0.5*p (0x4bca56 mulsd then 0x4bca5b subsd with the constant 0.5 at 0x4bca44), the result is '
       u'compared against zero (0x4bca60) and the same function asserts defect_reduction > 0.0, and x '
       u'comes from the three-instruction getter 0x4f9c30 = movsd xmm0,[rcx+0x58]. INFERRED: what that '
       u'field measures and where p comes from -- the reader is on the equivalent-problem side, not a '
       u'Part, and +0x58 belongs to a record of consecutive doubles that 0x827f0 copies wholesale '
       u'(findings_equivalent.md sections 7-14). lcns now implements the FORM in '
       u'include/lcns/equivalent.hpp + src/equivalent.cpp with test_recovered asserting it, which is why '
       u'this is Structural rather than NotReversed: the formula is represented in code, its inputs are '
       u'not yet understood"},\n')
r = r.replace(A, ENT + A, 1)
io.open(RP, "w", encoding="utf-8", newline="\n").write(r)
txt = io.open(RP, encoding="utf-8", newline="").read().replace("\r\n","\n")
blk = txt[txt.index("inline constexpr Gap kGaps[]"):]; blk = blk[blk.index("{")+1: blk.index("\n};")]
hd = re.compile(r'\s*\{"([^"]+)",\s*Status::(\w+),')
ids, st = [], {}
for ln in blk.split("\n"):
    if ln.lstrip().startswith("//"): continue
    m = hd.match(ln)
    if m: ids.append(m.group(1)); st[m.group(2)] = st.get(m.group(2),0)+1
assert len(ids) == len(set(ids)), "dupes"
print("registry: %d entries, %s" % (len(ids), dict(sorted(st.items()))))
T = r"D:\Nesting\nestfab\lcns\tests\test_recovered.cpp"
s = io.open(T, encoding="utf-8", newline="").read()
s = re.sub(r"CHECK\(kGapCount == \d+\);", "CHECK(kGapCount == %d);" % len(ids), s)
for k in ("Recovered","Structural","Substituted","NotReversed"):
    s = re.sub(r"CHECK\(countOf\(Status::%s\) == \d+\);" % k, "CHECK(countOf(Status::%s) == %d);" % (k, st.get(k,0)), s)
io.open(T, "w", encoding="utf-8", newline="\n").write(s)
print("test counts synced")
subprocess.run(["git","-C",r"D:\Nesting\nestfab","add","-A"])
c = subprocess.run(["git","-C",r"D:\Nesting\nestfab","commit","-q","-m",
   "lcns: implement the recovered defect reduction (x - 0.5*p, asserted > 0) with tests"],
   capture_output=True, text=True)
print((c.stdout or c.stderr).strip()[:200] or "committed")
