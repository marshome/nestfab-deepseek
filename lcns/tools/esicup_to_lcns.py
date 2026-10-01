# -*- coding: utf-8 -*-
"""Convert an ESICUP / OR-Datasets "2D irregular" instance (JSON) into an lcns problem.json.

Input format (Oscar-Oliveira/OR-Datasets, Cutting-and-Packing/2D-Irregular):
    { "name": "swim",
      "items": [ { "id": 0, "demand": 3, "dxf": "...", "allowed_orientations": [0.0, 180.0],
                   "shape": { "type": "simple_polygon", "data": [[x, y], ...] } } ],
      "strip_height": 5752.0 }

The original polygons are in a down-right frame (y negative), so every polygon is normalised to a
non-negative local frame (bbox min at the origin) before being written out.

The strip has a FIXED side (`strip_height`) and an unbounded other side. lcns needs a finite sheet,
so the unbounded side is set to `length_mult * totalArea / strip_height` plus the largest part
extent, and the achieved length is measured afterwards from the bounding box of the solution.
Density is then `sum(part areas) / (fixed side * achieved length)` -- the same definition the
cutting & packing literature uses, which is what makes the comparison with published results valid.
"""
import argparse
import json
import math
import os
import sys


def ring_area(ring):
    a = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def polygon_area(outer, inners):
    a = abs(ring_area(outer))
    for h in inners:
        a -= abs(ring_area(h))
    return max(a, 0.0)


def bbox(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def load_instance(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def convert(inst, gap=0.0, length_mult=2.5, margin=1.15):
    H = float(inst["strip_height"])
    parts, total_area, max_extent = [], 0.0, 0.0

    for it in inst["items"]:
        shape = it["shape"]
        stype = shape.get("type", "simple_polygon")
        if stype == "simple_polygon":
            outer = [list(map(float, p)) for p in shape["data"]]
            inners = []
        elif stype in ("polygon_with_holes", "polygon"):
            outer = [list(map(float, p)) for p in shape["data"]["outer"]]
            inners = [[list(map(float, p)) for p in h] for h in shape["data"].get("holes", [])]
        else:
            raise SystemExit("unsupported shape type: %s" % stype)

        x0, y0, x1, y1 = bbox(outer)
        dx, dy = -x0, -y0
        outer = [[p[0] + dx, p[1] + dy] for p in outer]
        inners = [[[p[0] + dx, p[1] + dy] for p in h] for h in inners]
        # keep every ring counter-clockwise (lcns treats the first ring as the outer boundary)
        if ring_area(outer) < 0:
            outer.reverse()
        for h in inners:
            if ring_area(h) > 0:
                h.reverse()

        area = polygon_area(outer, inners)
        total_area += area * int(it["demand"])
        max_extent = max(max_extent, x1 - x0, y1 - y0)
        parts.append({
            "id": int(it["id"]),
            "multiplicity": int(it["demand"]),
            "priority": 0,
            "extra_gap": float(gap),
            "shape": [{"external": outer, "inners": inners}],
        })

    # the unbounded direction: a generous X extent so the strip is effectively infinite
    L = length_mult * total_area / max(H, 1e-9) + margin * max_extent
    L = float(math.ceil(L))

    problem = {
        "source_version": "lcns/0.1 (converted from ESICUP/OR-Datasets)",
        "objective": 3,                 # MinimizeArea (see model.hpp Objective)
        "nesting_origin": 0,            # bottom-left
        "interpart_gap": float(gap),
        "parts": parts,
        "sheets": [{
            "id": 0, "width": L, "height": H, "quantity": 1, "price": 0.0,
            "priority": 0, "non_rectangular": False, "reusable": True,
        }],
    }
    meta = {
        "name": inst.get("name", os.path.basename(path_src)),
        "strip_height": H,
        "fixed_axis": "y",
        "sheet_length": L,
        "total_part_area": total_area,
        "part_kinds": len(parts),
        "part_instances": sum(p["multiplicity"] for p in parts),
        "max_part_extent": max_extent,
        "orientations": sorted({tuple(it.get("allowed_orientations", [])) for it in inst["items"]},
                               key=lambda t: (len(t), t)),
    }
    return problem, meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--meta", dest="meta")
    ap.add_argument("--gap", type=float, default=0.0)
    ap.add_argument("--length-mult", type=float, default=2.5)
    a = ap.parse_args()

    path_src = a.inp
    inst = load_instance(a.inp)
    prob, meta = convert(inst, gap=a.gap, length_mult=a.length_mult)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(prob, f)
    if a.meta:
        with open(a.meta, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=1)
    print("%-10s parts=%d instances=%d area=%.1f  H=%.1f  L=%.1f"
          % (meta["name"], meta["part_kinds"], meta["part_instances"],
             meta["total_part_area"], meta["strip_height"], meta["sheet_length"]))
