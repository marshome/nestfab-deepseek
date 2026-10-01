# -*- coding: utf-8 -*-
"""Layout sanity check for every docs/*.svg produced by gen_arch.py / gen_flow.py.

Reports: boxes outside the canvas, overlapping sibling boxes, text/lines outside the canvas, and
connector segments that pass through a box they do not belong to (the classic flowchart defect).
"""
import glob
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "docs")
NS = "{http://www.w3.org/2000/svg}"

total = 0
for path in sorted(glob.glob(os.path.join(DOCS, "*.svg"))):
    name = os.path.basename(path)
    root = ET.parse(path).getroot()
    W, H = float(root.get("width")), float(root.get("height"))
    rects, texts, paths = [], [], []
    polys = []                                   # (points, bbox) for diamonds / parallelograms
    for el in root.iter():
        tag = el.tag.replace(NS, "")
        if tag == "rect":
            try:
                x, y = float(el.get("x", 0)), float(el.get("y", 0))
                w, h = float(el.get("width", 0)), float(el.get("height", 0))
            except ValueError:
                continue
            if w < W and h < H:
                rects.append((x, y, w, h))
        elif tag == "polygon":
            pts = [tuple(float(v) for v in p.split(","))
                   for p in el.get("points", "").strip().split()]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            polys.append((pts, (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))))
        elif tag == "text":
            texts.append((float(el.get("x")), float(el.get("y")), (el.text or "")[:24]))
        elif tag == "path":
            d = el.get("d", "")
            nums = []
            for tok in d.replace("M", " ").replace("L", " ").split():
                try:
                    nums.append(float(tok))
                except ValueError:
                    pass
            pts = list(zip(nums[0::2], nums[1::2]))
            if len(pts) >= 2:
                paths.append(pts)

    boxes = [b for b in rects if not (b[2] < 120 and b[3] < 22)] + [pb for _p, pb in polys]
    problems = []

    def hit(k, px, py, pad):
        """True if (px,py) is inside box k, using the real polygon for diamonds."""
        b = boxes[k]
        if k >= len(rects):                     # a polygon: exact point-in-polygon
            pts = polys[k - len(rects)][0]
            inside_flag = False
            n = len(pts)
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 > py) != (y2 > py):
                    xin = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
                    if px < xin:
                        inside_flag = not inside_flag
            if not inside_flag:
                return False
            # shrink slightly so touching a vertex does not count
            return (b[0] + pad < px < b[0] + b[2] - pad and
                    b[1] + pad < py < b[1] + b[3] - pad)
        return b[0] + pad < px < b[0] + b[2] - pad and b[1] + pad < py < b[1] + b[3] - pad

    for x, y, w, h in boxes:
        if x < -0.5 or y < -0.5 or x + w > W + 0.5 or y + h > H + 0.5:
            problems.append("box outside canvas: (%.0f,%.0f %.0fx%.0f)" % (x, y, w, h))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            ax, ay, aw, ah = boxes[i]
            bx, by, bw, bh = boxes[j]
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                problems.append("boxes overlap: (%.0f,%.0f) vs (%.0f,%.0f)" % (ax, ay, bx, by))
    for x, y, t in texts:
        if x < 0 or y < 0 or x > W or y > H:
            problems.append("text outside canvas: %r (%.0f,%.0f)" % (t, x, y))

    for pts in paths:
        ends = [pts[0], pts[-1]]
        touched = set()
        for k in range(len(boxes)):
            b = boxes[k]
            for e in ends:
                # an endpoint belongs to a box if it is on/next to that box's bounding box
                # (a diamond's vertex is not "inside" the polygon by ray casting, so use the bbox)
                if (b[0] - 6 < e[0] < b[0] + b[2] + 6 and b[1] - 6 < e[1] < b[1] + b[3] + 6):
                    touched.add(k)
        found = False
        for si in range(len(pts) - 1):
            (x1, y1), (x2, y2) = pts[si], pts[si + 1]
            steps = max(2, int(max(abs(x2 - x1), abs(y2 - y1)) / 5))
            for s in range(1, steps):
                px = x1 + (x2 - x1) * s / steps
                py = y1 + (y2 - y1) * s / steps
                for k in range(len(boxes)):
                    if k in touched:
                        continue
                    if hit(k, px, py, pad=1.5):
                        b = boxes[k]
                        problems.append("connector crosses box (%.0f,%.0f %.0fx%.0f) at (%.0f,%.0f)"
                                        % (b[0], b[1], b[2], b[3], px, py))
                        found = True
                        break
                if found:
                    break
            if found:
                break

    print("%-22s %.0fx%.0f  boxes=%2d paths=%2d -> %s"
          % (name, W, H, len(boxes), len(paths),
             "OK" if not problems else "%d PROBLEM(S)" % len(problems)))
    seen = set()
    for pr in problems:
        if pr in seen:
            continue
        seen.add(pr)
        print("      " + pr)
    total += len(seen)

print("total distinct problems:", total)
sys.exit(1 if total else 0)
