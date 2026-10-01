# -*- coding: utf-8 -*-
"""Run the ESICUP/OR-Datasets irregular instances through lcns and compare with the literature.

Usage:
    python tools/run_benchmarks.py [--time 20] [--seeds 1] [--only SWIM,SHAPES0] [--lcns <dir>]

Published values are taken from the LaTeX source of
    Gardeyn, Vanden Berghe, Wauters: "An open-source heuristic to reboot 2D nesting research",
    European Journal of Operational Research (arXiv:2509.13329v3),
which is the current state of the art on exactly these instances (TAB:best / TAB:comparison).
They are quoted, not recomputed: see datasets/refs/ for the downloaded source.

Density convention (must match the literature for the comparison to mean anything):
    rho = sum(placed part areas) / (fixed_strip_side * achieved_length)
The instances fix `strip_height` (the y extent) and leave x unbounded; the achieved length is the
x extent of the bounding box of the placed parts.
"""
import argparse
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATASETS = os.path.abspath(os.path.join(ROOT, "..", "datasets"))
ORJSON = os.path.join(DATASETS, "or-datasets", "or", "Cutting-and-Packing", "2D-Irregular",
                      "Datasets")
WORK = os.path.join(DATASETS, "work")

# --- published results: arXiv:2509.13329v3, Table "best_known_table" ------------------------------
# (sparrow 20 min  vs  previous best known, with the algorithm that produced it)
BEST = {
    "ALBANO":   (89.82, 89.58, "E"),
    "DAGLI":    (90.17, 89.51, "E"),
    "FU":       (92.41, 92.41, "E"),
    "JAKOBS1":  (89.26, 89.09, "L/E/W/S"),
    "JAKOBS2":  (87.73, 87.73, "E/S"),
    "MAO":      (86.87, 86.05, "S"),
    "MARQUES":  (92.02, 91.02, "S"),
    "SHAPES0":  (69.98, 68.79, "E/W/S"),
    "SHAPES1":  (76.73, 76.73, "E/S"),
    "SHAPES2":  (86.23, 84.84, "E"),
    "SHIRTS":   (90.92, 88.96, "E/W"),
    "SWIM":     (79.83, 75.94, "E"),
    "TROUSERS": (92.62, 91.06, "S"),
}
# --- published expected density E(rho): arXiv:2509.13329v3, "comparison_table" --------------------
# sparrow (100 runs x 20 min) | ROMA | GCS | FLD | ELS | PS(open source)
COMPARE = {
    "ALBANO":   (89.47, 87.55, 87.47, 88.01, 87.38, 84.95),
    "DAGLI":    (89.26, 87.50, 87.06, 87.14, 86.27, 84.17),
    "FU":       (92.24, 91.95, 90.68, 91.17, 90.00, 90.39),
    "JAKOBS1":  (89.09, 89.09, 88.90, 88.96, 88.35, 81.67),
    "JAKOBS2":  (84.77, 83.56, 81.14, 83.41, 80.97, 80.42),
    "MAO":      (86.14, 83.76, 82.93, 82.28, 82.57, 75.94),
    "MARQUES":  (90.93, 89.97, 89.40, 88.38, 88.32, 85.48),
    "SHAPES0":  (68.60, 68.73, 67.26, 67.39, 66.85, 66.50),
    "SHAPES1":  (75.69, 75.86, 73.79, 73.91, 74.24, 72.55),
    "SHAPES2":  (84.68, 83.02, 82.40, None, 82.55, 85.49),
    "SHIRTS":   (89.66, 87.62, 87.59, 88.21, 87.20, 85.99),
    "SWIM":     (78.26, 74.29, 74.49, 74.66, 74.10, 71.44),
    "TROUSERS": (91.73, 90.48, 89.02, 89.17, 88.29, 89.30),
}
# dataset folder -> the instance names used in the published tables
FAMILY = {
    "ALBANO": {"ALBANO": "albano.json"},
    "BLAZ": {"SHAPES2": "blaz1.json"},
    "DAGLI": {"DAGLI": "dagli.json"},
    "FU": {"FU": "fu.json"},
    "JAKOBS": {"JAKOBS1": "jakobs1.json", "JAKOBS2": "jakobs2.json"},
    "MAO": {"MAO": "mao.json"},
    "MARQUES": {"MARQUES": "marques.json"},
    "SHAPES": {"SHAPES0": "shapes0.json", "SHAPES1": "shapes1.json"},
    "SHIRTS": {"SHIRTS": "shirts.json"},
    "SWIM": {"SWIM": "swim.json"},
    "TROUSERS": {"TROUSERS": "trousers.json"},
}


def find_instance(family, fname):
    hits = glob.glob(os.path.join(ORJSON, family, "json", "**", fname), recursive=True)
    if hits:
        return hits[0]
    hits = glob.glob(os.path.join(ORJSON, family, "**", fname), recursive=True)
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time", type=float, default=20.0)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--iterations", type=int, default=100000)
    ap.add_argument("--only", default="")
    ap.add_argument("--build", default=os.path.join(ROOT, "build"))
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()

    exe = os.path.join(a.build, "nest_eval.exe")
    if not os.path.exists(exe):
        raise SystemExit("build nest_eval first: %s" % exe)
    os.makedirs(WORK, exist_ok=True)

    only = {s.strip().upper() for s in a.only.split(",") if s.strip()}
    rows = []
    for family, insts in sorted(FAMILY.items()):
        for name, fname in sorted(insts.items()):
            if only and name not in only:
                continue
            src = find_instance(family, fname)
            if not src:
                print("MISSING instance %s (%s)" % (name, fname))
                continue
            prob = os.path.join(WORK, name.lower() + ".json")
            meta = os.path.join(WORK, name.lower() + ".meta.json")
            subprocess.run([a.python, os.path.join(HERE, "esicup_to_lcns.py"),
                            "--in", src, "--out", prob, "--meta", meta], check=True,
                           stdout=subprocess.DEVNULL)
            with open(meta, "r", encoding="utf-8") as f:
                m = json.load(f)

            best_rho, best_len, worst = None, None, None
            for seed in range(a.seeds):
                out = subprocess.run([exe, prob, "--time", str(a.time), "--seed", str(seed),
                                      "--iterations", str(a.iterations), "--csv"],
                                     capture_output=True, text=True, check=True).stdout.strip()
                _path, total, nested, placed, bw, bh, fill, used, secs, cancelled = out.split(",")
                total, nested = int(total), int(nested)
                placed, bw, bh, secs = float(placed), float(bw), float(bh), float(secs)
                # fixed side is y (strip_height), achieved length is along x
                length = bw
                rho = placed / (m["strip_height"] * length) if length > 0 else 0.0
                if rho > (best_rho or -1):
                    best_rho, best_len = rho, length
                    worst = (seed, nested, total, secs, cancelled)
            pub, prev, who = BEST[name]
            # sanity check of the density convention: the length implied by the published rho
            implied = m["total_part_area"] / (m["strip_height"] * pub / 100.0)
            rows.append({
                "name": name, "family": family, "kinds": m["part_kinds"],
                "instances": m["part_instances"], "area": m["total_part_area"],
                "H": m["strip_height"], "sheet_L": m["sheet_length"],
                "lcns_rho": best_rho * 100.0, "length": best_len,
                "nested": worst[1], "total": worst[2], "secs": worst[3],
                "pub": pub, "prev": prev, "who": who, "implied_L": implied,
                "max_extent": m["max_part_extent"], "seed": worst[0],
                "cancelled": worst[4],
            })
            print("%-9s nested=%3d/%3d  rho=%5.2f%%  pub=%5.2f%%  impliedL=%8.1f maxExtent=%7.1f"
                  % (name, worst[1], worst[2], best_rho * 100.0, pub, implied,
                     m["max_part_extent"]))

    if not rows:
        raise SystemExit("no instances run")

    # --- results.csv ---------------------------------------------------------------------------
    csv = os.path.join(DATASETS, "results.csv")
    with open(csv, "w", encoding="utf-8") as f:
        f.write("instance,family,part_kinds,part_instances,total_area,strip_height,sheet_length,"
                "nested,total_instances,lcns_rho_pct,lcns_length,seconds,seed,"
                "published_best_rho_pct,previous_best_rho_pct,previous_by,"
                "literature_implied_length,max_part_extent\n")
        for r in rows:
            f.write("{name},{family},{kinds},{instances},{area:.3f},{H:.3f},{sheet_L:.1f},"
                    "{nested},{total},{rho:.4f},{length:.3f},{secs:.3f},{seed},"
                    "{pub:.2f},{prev:.2f},{who},{implied_L:.1f},{max_extent:.1f}\n".format(
                        rho=r["lcns_rho"], **{k: v for k, v in r.items() if k != "lcns_rho"}))
    print("wrote", csv)

    # --- RESULTS.md ----------------------------------------------------------------------------
    md = os.path.join(DATASETS, "RESULTS.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("# lcns on the ESICUP / OR-Datasets 2D irregular benchmarks\n\n")
        f.write("Published reference values are **quoted** from the LaTeX source of Gardeyn, "
                "Vanden Berghe & Wauters, *An open-source heuristic to reboot 2D nesting "
                "research*, European Journal of Operational Research (arXiv:2509.13329v3) -- "
                "downloaded to `refs/` -- which reports the current state of the art on exactly "
                "these instances.\n\n")
        f.write("`rho = sum(placed part areas) / (strip_height * achieved_length)`, the density "
                "definition used in that literature. The instances fix `strip_height` and leave "
                "the other axis unbounded; lcns is given an over-long sheet and the achieved "
                "length is measured from the bounding box of the placed parts.\n\n")
        f.write("| instance | part kinds | instances | total area | strip H | nested | lcns rho | "
                "previous best rho | sparrow rho | gap vs sparrow | secs |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for r in rows:
            gap = r["pub"] - r["lcns_rho"]
            f.write("| `%s` | %d | %d | %.0f | %.0f | %d/%d | **%.2f%%** | %.2f%% | %.2f%% | "
                    "%.2f pp | %.1f |\n"
                    % (r["name"], r["kinds"], r["instances"], r["area"], r["H"],
                       r["nested"], r["total"], r["lcns_rho"], r["prev"], r["pub"], gap,
                       r["secs"]))
        f.write("\n## Literature comparison on the same instances "
                "(published expected density, %)\n\n")
        f.write("| instance | sparrow | ROMA | GCS | FLD | ELS | PS | lcns |\n")
        f.write("|---|---:|---:|---:|---:|---:|---:|---:|\n")
        for r in rows:
            c = COMPARE[r["name"]]
            fmt = lambda v: ("%.2f" % v) if v is not None else "-"
            f.write("| `%s` | %s | %s | %s | %s | %s | %s | **%.2f** |\n"
                    % (r["name"], fmt(c[0]), fmt(c[1]), fmt(c[2]), fmt(c[3]), fmt(c[4]),
                       fmt(c[5]), r["lcns_rho"]))
        f.write("\nLegend: ROMA = Sato et al. 2019 (raster), GCS = Elkeran 2013, "
                "FLD = Wang et al. 2017, ELS = Leung et al. 2012, PS = Fontan 2023 "
                "(open source, deterministic). All quoted from the same table.\n\n")
        f.write("## What this comparison does and does not say\n\n")
        f.write("* The published numbers come from **20-minute runs** (sparrow: 100 independent "
                "runs; the deterministic PS: one run). The lcns column here comes from a single "
                "short run per instance -- see `results.csv` for the exact budget (`seconds`) and "
                "seed. It is a **reproducible baseline**, not a claim of parity.\n")
        f.write("* `sparrow` searches **continuous rotations** and uses a dedicated collision "
                "detection engine (`jagua-rs`). lcns is a reverse-engineered reconstruction whose "
                "geometry kernel is a hand-written fixed-point reimplementation and whose LP "
                "backend is a zero-dependency simplex (the original statically links COIN-OR "
                "Clp 1.15.3) -- so a gap is expected and is documented rather than hidden.\n")
        f.write("* lcns does not honour the per-item `allowed_orientations` of the instances; it "
                "uses its own discrete angle ladder (`--angles`).\n")
        f.write("* `literature_implied_length` in `results.csv` is "
                "`total_area / (strip_height * published_rho)`: it is the length the published "
                "density implies, and is printed so the density convention can be sanity checked "
                "independently (it must exceed the largest part extent).\n")
    print("wrote", md)


if __name__ == "__main__":
    main()
