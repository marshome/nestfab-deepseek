# NOTES — shared recon for the cutting-technology feature investigation

Read `D:\Nesting\nestfab\re\BRIEF.md` first.  This file adds the practical ABI facts and
tooling that were recovered before the per-group work started.  Everything here is
**proven** by disassembly unless marked inferred.

## 0. Environment / tooling

* Python: `C:\Users\16479\AppData\Local\Python\bin\python.exe` (3.14 — plain `python` is NOT on PATH).
* `re\lib.py` was fixed in place (its docstring had a bad `\N` escape that Python 3.14 rejects).
  Use: `sys.path.insert(0, r'D:\Nesting\nestfab\re'); from lib import *`
* Helper scripts written for this task (all under `D:\Nesting\nestfab\re\feat\`):
  * `d.py RVA [lo hi]` — annotated disassembly of the function containing RVA.  RIP-relative
    operands are resolved to `STR:"..."`, `FN:<export name>`, `infn@0x...`.  Call targets are
    resolved to export names when known.
  * `dmp.py RVA...` — same but writes to `feat\out_dis.txt` (so you can grep it).
  * `xr.py 0x9AD... | substr` — which functions reference a given string RVA / substring
    (uses `prof2.pkl` `data_refs`).
  * `rng.py 0x9DA300 0x9DB000` — dump all C strings in an RVA range.
  * `findstr.py <regex>...` — regex search over all strings.
  * `tables.py rva...` — search for a run of 8-byte pointers to those string RVAs (enum tables).
  * `fields.py` — writes `feat\out_fields.txt`: for every export, the raw stores seen through
    the `this` pointer (offset table).
  * `map_targets.py` — writes `feat\targets.tsv` (name → RVA/size/ordinals/strings).
  * `keymap.py` — tries to map JSON schema keys to internal getter/setter field offsets.

## 1. Calling convention / common code shape (PROVEN)

All 168 exports are plain `__cdecl` x64 functions (rcx, rdx, r8, r9, then stack; `xmm0..3`).
Two shapes exist:

**(a) "guarded" API function** (most `SetXxx` that take an enum + scalar):
```
push ...; mov rdi, rcx          ; rdi = object ("this")
mov ebp, edx                    ; ebp = int argument
movapd xmm6, xmm2               ; doubles
call 0xAB20                     ; -> some guard/lock context (LaunchingOrder lock)
call 0x63F6C0                   ; validity check (nonzero -> throw)
call 0x1BF40                    ; get dbg::symlog sink; then logs "-> ", "<Name>", ...
...
mov dword ptr [rdi+0xNN], ebp   ; THE ACTUAL EFFECT
ret
```
The `dbg::symlog` logging is noise; **only the final `mov [rdi+off], reg` matters.**
(0x978010 appends to the log string, 0x869D00/0x868F70 print ints, 0x1C0C0 prints doubles.)

**(b) "structure-layer" function** (small; `rcx` is the structure object directly, no guard):
```
mov rsi, rcx ; mov ebx, edx
lea rcx, [rip+S]  ; S = own __func__ literal
call 0x64E120 / 0x64ABF0 / 0x64CA50   ; dbg::symlog constructor variants
mov dword ptr [rsi+0xNN], ebx
ret
```

So: **the first argument of nearly every recovered export is a pointer to a "structure"
object, and the export writes one field of it.**  The structure objects come in three kinds:
`Order` (the problem/launching order), `Sheet`, `Part` (and `PartVariant`, `Nesting`, …).

## 2. Recovered structure field offsets (PROVEN, from `feat\out_fields.txt`)

Only offsets reachable from raw stores are listed; the same offset number can belong to
different classes, so **always identify the object from the function that writes it**.

Order / problem level (`SetXxxMode`, common cut, multitorch, row, pipe, leather, marks, …):
```
Order+0x08  objective (int, see enum table below)          <- SetObjective
Order+0x28,0x30,0x38  offcut evaluation (3 doubles)        <- SetOffcutEvaluation
Order+0x44  shear (mode int)                               <- SetShearMode / SetPartialShearMode
Order+0x48  partial shear (int)                            <- SetPartialShearMode (also writes 0x44)
Order+0x50  shear_gap (double)                             <- SetShearGap
Order+0x58  shear_repulse_from_borders (int)               <- SetShearRepulseFromBorders
Order+0x5c  common_cut mode (bool)                         <- SetCommonCutMode
Order+0x60  common cut double (tolerance/width)            <- SetCommonCutMode
Order+0x68  "common cut safety preference set" (byte=1)    <- SetCommonCutSafetyPreference
Order+0x6c  common_cut_safety_preference (int)             <- SetCommonCutSafetyPreference
Order+0x70,0x78  two doubles                               <- SetCommonCutAuthorizations
Order+0x80  int                                            <- SetCommonCutAuthorizations (r9d)
Order+0x88  "cutting preference set" tag (1=int mode / 0=objective mode)
Order+0x8c  common_cut_cutting_preference (int)            <- SetCommonCutCuttingPreference
Order+0x90  common cut objective (double)                  <- SetCommonCutObjective(xmm2/xmm1 ratio)
Order+0x98  "multitorch cutting preference set" tag (1/0)
Order+0x9c  multitorch_cutting_preference (int)            <- SetMultiTorchCuttingPreference
Order+0xa8  int                                            <- SetMultiTorchMode
Order+0xb0,0xb8,0xd8  multitorch objective doubles         <- SetMultiTorchObjective
Order+0xc0,0xc8  multitorch mode doubles                   <- SetMultiTorchMode
Order+0x118 defect_gap (double)                            <- SetDefectGap
Order+0x120 sheet priority default? (int)                  <- SetSheetPriority
Order+0x124/0x128 specific sheet origin flag/value         <- SetSpecificSheetOrigin
Order+0x12c/0x130 specific sheet objective flag/value      <- SetSpecificSheetObjective
Order+0x138 sheet price (double)                           <- SetSheetPrice
Order+0x1f8 (incompatible sheet list ptr)                  <- SetIncompatibleSheet
Order+0x1f8,0x1fc local engine max threads/iterations      <- SetLocalMaximumThreads/Iterations
Order+0x200,0x201 local engine flags                       <- SetLocalEngine
Order+0x204,0x208 local engine threads                     <- SetLocalEngineThreads
Order+0x220..0x238 extra parameters (a std::map/JSON)      <- SetExtraParameters
Order+0x240 automatic stop (int)                           <- SetAutomaticStop
Order+0x128..0x150 row mode (5 pointers/doubles + flag)    <- SetRowMode
Order+0x158..0x178 pipe mode (5 values)                    <- SetPipeMode
Order+0x108 leather mode (int)                             <- SetLeatherMode
Order+0xe8,0xf0 mark size / inter-distance (2 doubles)     <- SetMarkMode
```
Sheet level (writes seen through a Sheet*): `+0x08 objective(int)`, `+0x44/0x48 shear`,
`+0x50 shear_gap(double)`, `+0x58 shear_repulse_from_borders(int)`,
`+0xf8/0x100/0x108/0x110 left/right/bottom/top gap (4 doubles)`, `+0x118 defect_gap`,
`+0x120 priority(int)`, `+0x124/0x128 specific origin`, `+0x12c/0x130 specific objective`,
`+0x138 price(double)`.

Part level: `+0x04 optional quantity(int)`, `+0x08 priority(int)`, `+0x10 extra_gap(double)`,
`+0x1c common cut mode(bool)`, `+0x88 open cutting path list`, `+0x188/0x190/0x198 authorizations`,
`+0x1a8 part-specific authorizations`, `+0x1e0 part variants`, `+0x20a/0x20b hole_status`
(ForcePartInsideHole sets 0x20a=1,0x20b=0; ForcePartOutsideHole at 0xC640 mirrors it),
`+0x2b0 assembly group list`.

> NOTE: the exact class of the object behind a given export must be checked per function
> (`d.py`).  Offsets `0x08/0x44/0x50/0x58` exist in more than one class.

## 3. The serialization schema — the authoritative field-name list (PROVEN)

`structure\text_io.cpp` (0x9DA694) saves/loads the whole problem as JSON
(`c:\Temp\cns.pb.json`).  Related functions:
* `SaveProblem` = **0x5070E0** (7663 bytes) — writes every key (uses getters, not raw offsets).
* `LoadProblem` = **0x50B1D0** — reads keys and calls internal setters.
* `SaveSheet` = 0x5091B0, `LoadSheet` = 0x5090A0, `SaveSolution` = 0x50DB70,
  `LoadSolution` = 0x50EE50, `LoadMtInfos` = 0x50A550/0x506350,
  `LoadCommonCutEvaluation` / `LoadSegment` / `LoadClusteredPart` (0x9DB0A0-B0D0).
Strings for the keys live at **0x9DA300-0x9DB010**.  Dump them with
`rng.py 0x9DA300 0x9DB010`.  Highlights (verbatim key names):

```
--- order/problem ---
extra_infos authorizations clustered_parts intergap requested_time layout_cost
max_active_parts max_different_sheets strict_part_priorities have_priority_interpenetration
priority_interpenetration assembly_group modules parts clusters sheets
--- sheet ---
quantity dimension_x dimension_y left_gap right_gap bottom_gap top_gap defect_gap
used_surface_evaluation used_surface_min_offcut_dimension used_surface_min_offcut_area
used_surface_usable_offcut_ratio optional_fill_unlimited evaluate_intermediate_as_last
nesting_origin grain_direction price priority sheet_quality_zones shear shear_corner
shear_repulse_from_borders shear_gap shear_thickness mark_active mark_size mark_inter_distance
floating origin_packing try_biggest_part_in_corner try_longest_part_in_corner
row_enable row_shear_gap row_shear_common_cut_gap row_punch_gap row_punch_common_cut_gap row_alternate
pipe_enable pipe_gap pipe_common_cut_gap pipe_border_common_cut pipe_border_gap
multitorch_allowed multitorch_nb_torches multitorch_min_torch_distance multitorch_max_torch_distance
multitorch_cutting_cost_per_unit multitorch_user_real_material_cost_per_unit
multitorch_reconfiguration_cost multitorch_vertical_torches
common_cut_allowed common_cut_gap common_cut_original_part_gap common_cut_cutting_cost_per_unit
common_cut_min_length common_cut_max_regarding_ratio common_cut_leadin_type
common_cut_no_holes common_cut_only_bi_modules
quality_zone_enable quality_zone_interactions
--- part ---
quantity max_quantity common_cutable extra_gap single_orientation
single_orientation_rot180_allowed force_bottom hole_status incompatible_sheets
--- nesting / solution ---
version number_of_nested_parts nestings sheet_id multiplicity angle flip
common_cut_evaluation common_cut number_of_common_cut common_cut_length regarding_length segments
left right left_index right_index valid linked number_of_groups fill_ratio
min_x min_y max_x max_y nested_parts evaluation_ratio used_surface nested_surface nested_string final
multitorch_infos multitorch_part_infos torch_distance group_number torch_number nb_active_torches
config_index info_nb_torches
```

## 4. Enum → string tables (PROVEN, decoded from the switch code in 0x511080)

`GetXxxProperties`-style dump function **0x511080** builds local `std::string[]` arrays and
indexes them (assert `index < size`), so the arrays give exact enum values:

* **objective** (getter sub_52F920): `0 MinimizeX, 1 MinimizeY, 2 NoOffcut, 3 MinimizeArea,
  4 MinimizeXThenY, 5 MinimizeYThenX, 6 IntelligentMinimizeX, 7 IntelligentMinimizeY`
  (0x9DB606..0x9DB676; `ERROR` for out of range).
* **nesting_origin** (getter sub_4F8F80): `0 BottomLeft, 1 TopLeft, 2 BottomRight, 3 TopRight`
  (0x9DB5C7.., `ERROR`).
* `CommonCutLeadinType(...)` printer at 0x9DC5B0; `EVALUATION(valid: linked: common_cut: quality:)`
  at 0x9DC54F.

## 5. The `boost` / `all_settings` preset maps (PROVEN, inside CreateProblem 0x1EE50)

`Structure::CreateProblem` = **0x1EE50** (15305 bytes, 3076 insns, RVA range 0x1EE50-0x22A39)
is the single place that turns the `Order` structure into the internal problem.  It is where
almost every feature flag is *enforced*.  Two `std::map<int,Properties>` presets exist:

* at 0x1EE50+0x3046 (`0x21F36`): `mov ecx, dword ptr [rdi + 0x9C]` with `rdi = Order*`,
  then a `std::map` tree search (`cmp ecx,[rdx+0x20]; left [rdx+0x10] / right [rdx+0x18]`).
  If not found → `assert(boost.find(order.multitorch_cutting_preference) != boost.end())`
  (string 0x9ADEE8) → then calls `GetMultitorchProperties` (0x9ADFA0).
  ⇒ `boost` maps an int "cutting preference" to a **MultitorchProperties** preset.
* at 0x1EE50+0x37A1 (`0x225F1`): `mov ecx, dword ptr [rax + 0x6C]` (Order+0x6C) then the same
  map search → `assert(all_settings.find(order.common_cut_safety_preference) != all_settings.end())`
  (0x9ADE98) → `GetCommonCutProperties` (0x9ADFC0).
  ⇒ `all_settings` maps an int "safety preference" to a **CommonCutProperties** preset.
  Both maps are populated earlier in 0x1EE50 from small **static tables** (a loop copying
  0x20-byte records into a `std::map`) around 0x21E1C and 0x224D5 — dump those loops to get the
  preset tables.  The 0x20-byte record layout appears to be
  `{int key; double a; double b; int c; bool d; bool e}` (inferred).

Other important internal names/rvas:
* `Structure::CreateProblem` **0x1EE50**; `ComputeSheetGeometryRowMode` string 0x9AE000;
  `ComputeNoHoleRings` 0x9ADFE0; `MakeClusterFromSuggestedPartsGrouping` 0x9AE040 (used by
  internal.cpp function **0x1C2A0**, called from **0x1C540**, itself called from 0x1EE50).
* `Structure::UnSerializeSolution` **0x1C5F0** (string 0x9AE120).
* `GetMultitorchProperties` / `GetCommonCutProperties` — names only (strings), implementations
  are small accessors inside the properties structs.
* `GetLayerRestrictedZonePart/Sheet`, `GetLayerLeatherPart/Sheet` (0x9AE070..0x9AE0D0) are used
  by **0x1C980** (2347 bytes, `../structure/border_property.hpp`, assert `quality >= 0 && quality < 9`)
  and by **0x7BF0C0** (266 bytes, `GetLayerLeatherPart`, `quality >= 0 && quality < 9`,
  `../structure/border_property.hpp`) and **0x1EE50**.
  Assert `quality >= 0 && quality < 100` (0x9ADDEA) also lives in 0x1C980 and 0x1EE50.
  ⇒ **two different quality ranges exist: 0..8 (9 levels, `border_property.hpp` layers) and
  0..99 (100 levels).**  Determine which is the leather quality zone and which the mark/other.
* `// BadCommonCutGaps` (0x9ADDD6) is used by **0x1C7C0**, a validator that also reports
  `// BadPartGeometry`, `// BadSheetGeometry`, `// BadSheetPrices`.
* `CommonCutEvaluation` printing: `EVALUATION(valid: linked: common_cut: quality:)` 0x9DC54F.
* `m_implementation->common_cut_properties.original_part_gap == 0.0` (0x9DA3D0) and
  `m_implementation->common_cut_computer.get()` (0x9DA4B8) — asserts in problem.cpp.
* `!!shear` (0x9BD4D1) and `part_number < m_common_cut_tiling_parts.size()` (0x9BD3D0) —
  asserts in the tiling/compact code.
* `enable_common_cut_nesting`, `enable_common_cut_relax_objective`, `enable_common_cut_repair`,
  `enable_common_cut_tiling`, `enable_common_cut_filling`, `enable_beautifier_common_cut`,
  `enable_beautifier_improve_common_cut`, `use_multitorch_tiling` — **extra parameter names**
  (0x9B009C-0x9B02EF), i.e. keys accepted by `SetExtraParameters`.
* `false && "internal error mode not yet supported with grain"` (0x9D9400) — grain constraint.
* `../structure/multitorch_eval.cpp` 0x9DBE30, `ComputeBestConfigSequence` 0x9DBE70,
  `!torch_configs.empty()` 0x9DBE17, `nb_torches_configs` 0x9DB76B — multitorch evaluation.
* `Structure::Box`, `GetPartTypicalDimension` 0x9DBB90, `FillRatio` 0x9DBBB8,
  `UsedSurfaceAux` 0x9DBBA8, `UsedSurfaceWithStairs` 0x9DBBD0 — stats (`..\structure\stats.cpp`).
* SVG/HTML reporting: `..\structure\svg_io.cpp` 0x9DB234, `DrawSVG` 0x9DB948,
  `DrawSVGReusableOffcuts` 0x9DB950, `DrawSVGMarks` 0x9DB968, `GetLeatherLayer` 0x9DB980,
  `DrawSVGAux` 0x9DB990, `DrawHtmlPartsTable` 0x9DB900, `GetNestingInformation` 0x9DB920,
  `DrawDxf` 0x9DB938/0x9DB940, `cns_solution.css` 0x9DB85C/0x9DB873/0x9DB887,
  `SHEET NOT FOUND: ` 0x9DBACB, `PART NOT FOUND: ` 0x9DBADD,
  `_border_` 0x9DB7BA, `__marks__` 0x9DB80B, `properties.active` 0x9DB815.

## 6. Rules for the write-up

* Language: **Chinese**; keep identifiers/enum names/technical terms in English.
* Every claim needs an RVA.  Mark clearly **【已证实】** (proven: read straight off the
  disassembly/strings) vs **【推断】** (inferred).
* Say what the function does, its parameter list (infer arity/types from the register use),
  where the value is stored, and where it is *consumed/enforced* (usually `CreateProblem` 0x1EE50,
  `Multi::*`, `Tiling::*`, `Row::*`, `Structure::*`).
* Prefer `d.py`/`dmp.py` output over guessing.
