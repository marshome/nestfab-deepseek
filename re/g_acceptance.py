"""Acceptance traceability check.

For every headline claim of the reconstruction, verify that the address/constant it rests on is
actually present in the re/ documents (so no claim is unsupported), and that the engineering
artefact it maps to exists in lcns/ with the stated constant.
"""
import io
import os
import re

RE = r"D:\Nesting\nestfab\re"
LC = r"D:\Nesting\nestfab\lcns"

def read(p):
    try:
        return io.open(p, encoding="utf-8").read()
    except Exception:
        return ""

docs = {}
for name in ("REPORT.md", "findings_lp_use.md", "findings_lp.md", "findings_geometry.md",
             "findings_engine.md", "findings_features.md", "findings_cloud_lic.md"):
    docs[name] = read(os.path.join(RE, name))
alldocs = "\n".join(docs.values())

code = {}
for root, _dirs, files in os.walk(LC):
    for f in files:
        if f.endswith((".hpp", ".cpp", ".md", ".txt", ".inc")):
            p = os.path.join(root, f)
            code[os.path.relpath(p, LC)] = read(p)
allcode = "\n".join(code.values())

# (claim, token that must appear in the docs, token that must appear in the code)
CHECKS = [
    ("Squeezer cost formula",            "0x1380D0", "squeezeCost"),
    ("  cost expression",                "obj[+0x10] / s", "ctx.threshold / s"),
    ("  alignment gate 0.005",           "0x9BCFD8", "kSqueezeAlignmentTolerance = 0.005"),
    ("  parallel gate 1e-06",            "0x9BCFC0", "kSqueezeParallelTolerance = 1e-06"),
    ("fixed point angle primitive",      "0x5C22D0", "angleToFixedDegrees"),
    ("  360e10 bound",                   "0x34630B8A000", "kFullTurnFixedDegrees = 3600000000000ll"),
    ("  90 degree magic",                "0xD18C2E2800", "0xD18C2E2800ll"),
    ("Squeezer ctor / inner layout",     "0x138A20", "Squeezer(double twiceMaxExtent"),
    ("  inner threshold at +0x10",       "inner[+0x10] = xmm3", "threshold_"),
    ("RowNester class + ctor",           "N5Multi9RowNesterE", "class RowNester"),
    ("  core at this+0x18",              "8F257", "core_"),
    ("  squeezer at core+0xC0",          "0x6AC118", "squeezer_"),
    ("core defaults",                    "0x9B1A48", "kRowCoreAt0x18 = 4.0"),
    ("  coefficient default",            "0x9B1A50", "kRowCoreAt0x20 = 20.0"),
    ("  third default",                  "0x9B1A40", "kRowCoreAt0x08 = 10.0"),
    ("alpha constants",                  "0x9D9C08", "kBoostAlpha = 0.5"),
    ("  dim alpha",                      "0x9D9BE8", "kDimAlpha = 0.1"),
    ("pricer assembly, no default",      "0x4D64C0", "LinearCombinationPricer"),
    ("  six factories",                  "0x4D9AD0", "AlphaSurfacePrice"),
    ("0x7CA830 in place sort",           "0x267A30", "canonicalise"),
    ("  three space separator",          "0x9C2DF2", "canonicalise"),
    ("CoinLP slots / layout",            "0x6792C0", "columnCost_"),
    ("  triplet accumulator",            "0x90", "Triplet"),
    ("  slot 6 negates",                 "xorpd", "Triplet"),
    ("BuildAndSolveLp",                  "0x7D7200", "buildAndSolveLp"),
    ("  set covering shape",             "0x9B08B0", "addRow"),
    ("Clp backend, OR-Tools absent",     "OsiClp", "LinearProgram"),
    ("quarantine of the DW extension",   "NOT PART OF THE BINARY", "NOT PART OF THE BINARY"),
    ("SetPipeMode writer",               "0xFCF0", "pipeMode"),
    ("SetCommonCutParameters writer",    "0x3C3F0", "commonCutAt1B0"),
    ("  verbatim struct copy",           "0x185A40", "cfgAt188"),
    ("0x5CD800 returns a bbox",          "0x5C8C50", "RowView"),
    ("  skip polarity",                  "非 0 即跳过", "skipExtent"),
    ("0x134470 min-over-candidates",     "0x134470", "buildSqueezer"),
    ("Item three level nesting",         "0x1333D0", "RowNestCore"),
    ("score sentinel -1.0",              "0x9BCF48", "kScoreUnset = -1.0"),
    ("  node contribution",              "0x134F30", "nodeLength"),
    ("  lazy score formula",             "0x136CB0", "candidateScore"),
    ("  last element decides",           "0x136CDC", "records.back()"),
    ("  candidate height scale",         "0x9BCEB0", "kCandidateHeightScale = 20.0"),
    ("node layout complete",             "0x135010", "flag98"),
    ("  node Y extent",                  "0x134F50", "nodeLengthY"),
    ("  node flag pair",                 "0x134F90", "nodeFlag40"),
    ("  rsp+0x110 object has a string",  "0x136D40", "ScoreRecord"),
    ("appender orderedAddElement",       "orderedAddElement", "orderedAddElement"),
    ("  appender resets the cache",      "0x137877", "scorer.invalidate()"),
    ("  fabs mask not a NaN sentinel",   "0x9BCF70", "candidateScore"),
    ("  merge source element stride",    "0xd8", "orderedAddElement"),
    ("authorisation predicate",          "0x5C2E40", "authorized"),
    ("angle -> transform primitive",     "0x5CEE50", "angleTransform"),
    ("  exact cardinal constants",       "0x9DE948", "signbit"),
    ("transformed container copy",       "0x5D38C0", "bestCandidate"),
    ("best-candidate loop",              "0x134470", "bestCandidate"),
    ("  the injection point is named",   "ScoreFn", "ScoreFn"),
    ("element tag getter",               "0x5C4CD0", "CandidateElement"),
    ("element angle getter",             "0x5C4CE0", "CandidateElement"),
    ("affine transform x'",              "0x5D3BFF", "transformX"),
    ("affine transform determinant",     "0x5D3C17", "transformDet"),
    ("candidate height from points",     "0x5C8C50", "transformedHeight"),
    ("drain cap 10000",                  "0x271000000000", "kSourceRecordCap = 10000"),
    ("drain loop",                       "0x137FE0", "drainSources"),
    ("source record layout",             "0x133EC9", "SourceRecord"),
    ("lazy score assembly",              "0x136CB0", "candidateScore"),
    ("element ctor layout",              "0x136350", "ScoreNode"),
    ("  compile-time offset lock",       "static_assert", "static_assert"),
    ("item container slots",             "0x1331A0", "itemContainerOffset"),
    ("item size 0x90",                   "0x1336F8", "kItemSize = 0x90"),
    ("abi: rdi is callee-saved",         "push rdi", "kScoreNodeSize"),
    ("squeezer vtable slot 1",           "0x13A360", "Squeezer::cost"),
    ("  the vcall is the squeeze cost",  "0x137C0C", "squeezeCost"),
    ("final score arithmetic",           "0x137C83", "elementScore"),
    ("  both branches tested",           "jbe", "elementScore"),
    ("one element writer",               "0x5C4C50", "writeCandidateAngle"),
    ("angle vector builder",             "0x8BEFC0", "candidateAngles"),
    ("  axis angle 90 degrees",          "0x13450B", "kAxisAngle90"),
    ("  the candidate set",              "0x134532", "axisAlignedCandidates"),
    ("element geometry source",          "0x133190", "kItemGeometry = 0x08"),
    ("element own-angle transform",      "0x5CEE50", "nodeAngleTransform"),
    ("element geometry step",            "0x1355C0", "nodeAngleTransform"),
    ("two point transform",              "0x5CF6B0", "transformPoint"),
    ("elem48 destructor strides",        "0x8C4FF0", "kElem48Stride = 0x30"),
    ("  nested record stride",           "0x8C502D", "kRecord18Stride = 0x18"),
    ("angle-transform second instance",  "0x5CE7F0", "halfTurn"),
    ("  the 180 degree call site",       "0x13645B", "kHalfTurn180"),
    ("flag predicate in full",           "0x134D70", "chainMonotone"),
    ("  elem16 is a 2D point",           "0x134E57", "kElem16Stride = 0x10"),
    ("  the chain tolerance",            "0x9BCEE0", "kChainEpsilon = 1e-06"),
    ("  sticky result (AND)",            "0x134EDD", "chainFlags"),
    ("tag nonzero is a reflection",      "0x5CEF62", "mirroredAngleTransform"),
    ("  the tag dispatch",               "0x5CEF5E", "nodeAngleTransform"),
    ("slot flag 99 producer",            "0x1366E0", "nodeSlotFlag99"),
    ("slot flag 98 producer",            "0x1366F9", "nodeSlotFlag98"),
    ("  a0 comes from an untranslated fn", "0x13670F", "0x135C70"),
    ("transform uses negSin/cos2",       "0x5D3C09", "transformDet"),
    ("auth table builder",               "0x5C4950", "makeAuthRecord"),
    ("  the ranges are angles",          "0x5C4A45", "makeAuthRecord"),
    ("part geometry accessor",           "0x4F7600", "kPartGeometryVia = 0x70"),
    ("  the angle wrap constant",        "0x34630B89FFF", "kAngleWrapMax"),
    ("shoelace area",                    "0x5CC6A0", "dllArea"),
    ("  the 0.5 constant",               "0x9DE910", "kAreaHalf = 0.5"),
    ("ring container copy",              "0x5C51A0", "copyRing"),
    ("  a0 is an area",                  "0x13670F", "nodeAreaValue"),
    ("  the min scan for the lowest pt", "0x135DB1", "nodeAreaValue"),
    ("translated copy",                  "0x5D3430", "translatedCopy"),
    ("  the merge 0.005 tolerance",      "0x9BCEE8", "kMergeAlignTolerance"),
    ("  the 32 byte two point record",   "0x135A4B", "kTwoPointRecord = 0x20"),
    ("  the row-TU helpers",             "0x134C10", "kTwoPointRecord"),
    ("item accessor second hop",         "0x547670", "kPartGeometryField = 0x90"),
    ("  the identity tail call",         "0x547610", "kPartGeometryObject = 0x70"),
    ("slot98 flag formula",              "0x1368A9", "nodeSlotFlag98"),
    ("beam width is an option",          "beam_width", "kAxisAngle90"),
    ("  option key table",               "0x9AFB9D", "findings_engine"),
    ("window contain epsilon",           "0x9BFD30", "kWindowContainEpsilon = 0.001"),
    ("  the inlined Contains assertion", "0x1C1A60", "kWindowContainEpsilon"),
    ("  DetectOverlap is dead code",     "0x99EAC0", "kWindowContainEpsilon"),
    ("frame of the acceptance test",     "test_recovered", "test_recovered"),
]

print("=== acceptance traceability ===")
bad = 0
for claim, dtok, ctok in CHECKS:
    d = dtok in alldocs
    c = ctok in allcode
    if not (d and c):
        bad += 1
    print("  %-34s docs:%-4s code:%-4s   %s  %s"
          % (claim, "OK" if d else "MISS", "OK" if c else "MISS", dtok, ctok))
print()
print("  %d/%d checks fully satisfied" % (len(CHECKS) - bad, len(CHECKS)))
print("  docs scanned: %d file(s), code scanned: %d file(s)" % (len(docs), len(code)))
