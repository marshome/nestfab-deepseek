# -*- coding: utf-8 -*-
"""Generate the main algorithm flowcharts as SVG (+ validate).

Run:  python tools/gen_flow.py

Each chart is data: nodes on a (col,row) grid and edges with optional labels. The router draws a
straight or elbow polyline with an arrowhead, so the diagrams stay readable without a layout engine.
"""
import io
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs")

FONT = "font-family=\"Segoe UI, Microsoft YaHei, Noto Sans CJK SC, sans-serif\""
MONO = "font-family=\"Cascadia Mono, Consolas, monospace\""
C_PROC, C_PROC_F = "#1f3a5f", "#eef4fb"
C_DEC, C_DEC_F = "#b45309", "#fff8ec"
C_END, C_END_F = "#1f4d3a", "#eefaf3"
C_IO, C_IO_F = "#5b2a86", "#f6eefc"
C_NOTE, C_NOTE_F = "#667085", "#f4f5f7"
C_LINE = "#7b8794"

CW, CH = 360, 62          # default node size
X0, Y0, DX, DY = 60, 116, 420, 104


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def node_box(col, row, kind, lines, span=1, h=None, w=None):
    x = X0 + col * DX
    y = Y0 + row * DY
    w = w or (CW + (span - 1) * DX)
    h = h or CH
    return x, y, w, h, kind, lines


def shape(x, y, w, h, kind):
    if kind == "dec":
        cx = x + w / 2
        return '<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="%s" stroke="%s" stroke-width="1.3"/>' % (
            cx, y, x + w, y + h / 2, cx, y + h, x, y + h / 2, C_DEC_F, C_DEC)
    if kind == "start" or kind == "end":
        return '<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s" stroke="%s" stroke-width="1.3"/>' % (
            x, y, w, h, h // 2, C_END_F, C_END)
    if kind == "io":
        k = 22
        return '<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="%s" stroke="%s" stroke-width="1.3"/>' % (
            x + k, y, x + w, y, x + w - k, y + h, x, y + h, C_IO_F, C_IO)
    if kind == "note":
        return '<rect x="%d" y="%d" width="%d" height="%d" rx="4" fill="%s" stroke="%s" ' \
               'stroke-width="1.1" stroke-dasharray="5,4"/>' % (x, y, w, h, C_NOTE_F, C_NOTE)
    return '<rect x="%d" y="%d" width="%d" height="%d" rx="5" fill="%s" stroke="%s" stroke-width="1.3"/>' % (
        x, y, w, h, C_PROC_F, C_PROC)


def text_in(x, y, w, h, lines, kind):
    out = []
    n = len(lines)
    if n == 1:
        ys = [y + h / 2 + 5]
    else:
        step = 17
        y0 = y + h / 2 - (n - 1) * step / 2 + 5
        ys = [y0 + i * step for i in range(n)]
    for i, (txt, mono) in enumerate(lines):
        fam = MONO if mono else FONT
        size = 11.5 if mono else 12.5
        weight = "600" if i == 0 else "400"
        color = "#10202f" if i == 0 else "#33404d"
        anchor = "middle" if kind in ("dec",) else "middle"
        out.append('<text x="%d" y="%.1f" %s font-size="%.1f" font-weight="%s" fill="%s" '
                   'text-anchor="%s">%s</text>' % (x + w / 2, ys[i], fam, size, weight, color,
                                                   anchor, esc(txt)))
    return "\n".join(out)


def route(a, b, label=None):
    """Connector router with three automatic modes:

    1. same column            -> a straight vertical (or horizontal) line;
    2. rows close together    -> a bus line half way between the two rows;
    3. a long jump / backward -> an orthogonal run through the gap between two columns,
       so the line never crosses an unrelated box.
    """
    ax, ay, aw, ah = a[:4]
    bx, by, bw, bh = b[:4]
    acx, acy = ax + aw / 2, ay + ah / 2
    bcx, bcy = bx + bw / 2, by + bh / 2
    if abs(acx - bcx) < 1.0:                                   # 1. same column
        if by > ay:
            segs = [(acx, ay + ah), (bcx, by)]
        elif by < ay:
            segs = [(acx, ay), (bcx, by + bh)]
        else:
            segs = [(ax + aw, acy), (bx, bcy)]
    elif abs(bcy - acy) <= 1.6 * DY:                            # 2. bus between the rows
        if by > ay:
            p1, p3 = (acx, ay + ah), (bcx, by)
        else:
            p1, p3 = (acx, ay), (bcx, by + bh)
        bus = (p1[1] + p3[1]) / 2
        segs = [p1, (p1[0], bus), (p3[0], bus), p3]
    else:                                                       # 3. lane in the column gap
        lane = ax + aw + 15 if bx > ax else ax - 15
        side_a = (ax + aw, acy) if bx > ax else (ax, acy)
        if abs(bcy - acy) < 1.0:
            # same row: a plain horizontal hop through the gap
            side_b = (bx, bcy) if bx > lane else (bx + bw, bcy)
            segs = [side_a, (lane, acy), (lane, bcy), side_b]
        else:
            # long jump: run up/down the lane, then enter the target row from above/below so
            # the final horizontal never crosses a sibling box in the target's row
            if bcy < acy:
                jun = by - 10
                side_b = (bcx, by)
            else:
                jun = by + bh + 10
                side_b = (bcx, by + bh)
            segs = [side_a, (lane, acy), (lane, jun), (bcx, jun), side_b]
    d = "M %.1f %.1f " % segs[0] + " ".join("L %.1f %.1f" % s for s in segs[1:])
    out = ['<path d="%s" fill="none" stroke="%s" stroke-width="1.4" marker-end="url(#ah)"/>'
           % (d, C_LINE)]
    if label:
        # place the label on the longest segment so it does not sit on a corner
        best, blen = 0, -1.0
        for i in range(len(segs) - 1):
            ln = abs(segs[i + 1][0] - segs[i][0]) + abs(segs[i + 1][1] - segs[i][1])
            if ln > blen:
                best, blen = i, ln
        mx = (segs[best][0] + segs[best + 1][0]) / 2
        my = (segs[best][1] + segs[best + 1][1]) / 2
        wl = 10 + 8 * len(label)
        out.append('<rect x="%.1f" y="%.1f" width="%d" height="17" rx="8" fill="#ffffff" '
                   'stroke="%s" stroke-width="0.9"/>' % (mx - wl / 2, my - 8.5, wl, C_LINE))
        out.append('<text x="%.1f" y="%.1f" %s font-size="11" fill="#33404d" '
                   'text-anchor="middle">%s</text>' % (mx, my + 4, FONT, esc(label)))
    return "\n".join(out)


def render(name, title, subtitle, nodes, edges, notes=()):
    boxes = {}
    for spec in nodes:
        nid, col, row, kind, lines = spec[0], spec[1], spec[2], spec[3], spec[4]
        span = spec[5] if len(spec) > 5 else 1
        h = spec[6] if len(spec) > 6 else None
        boxes[nid] = node_box(col, row, kind, lines, span=span, h=h)
    maxx = max(b[0] + b[2] for b in boxes.values())
    maxy = max(b[1] + b[3] for b in boxes.values())
    W = int(maxx + 60)
    note_h = 0
    if notes:
        note_h = 26 * len(notes) + 26
    H = int(maxy + 40 + note_h)

    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
             % (W, H, W, H),
             '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
             'markerHeight="7" orient="auto-start-reverse">'
             '<path d="M 0 0 L 10 5 L 0 10 z" fill="%s"/></marker></defs>' % C_LINE,
             '<rect width="100%%" height="100%%" fill="#ffffff"/>',
             '<text x="%d" y="42" %s font-size="22" font-weight="700" fill="#10202f">%s</text>'
             % (X0, FONT, esc(title)),
             '<text x="%d" y="68" %s font-size="12.5" fill="#55636f">%s</text>'
             % (X0, FONT, esc(subtitle))]
    for e in edges:
        parts.append(route(boxes[e[0]], boxes[e[1]], e[2] if len(e) > 2 else None))
    for nid, spec in boxes.items():
        x, y, w, h, kind, lines = spec
        parts.append(shape(x, y, w, h, kind))
        parts.append(text_in(x, y, w, h, lines, kind))
    y = maxy + 22
    for note in notes:
        parts.append('<text x="%d" y="%d" %s font-size="11.5" fill="#667085">%s</text>'
                     % (X0, y, FONT, esc(note)))
        y += 26
    parts.append('</svg>')
    p = os.path.join(OUT, name + ".svg")
    io.open(p, "w", encoding="utf-8", newline="\n").write("\n".join(parts))
    ET.parse(p)                     # must be well-formed
    return W, H


# =============================================================================
# 1. 端到端：建模 → 选项 → 云端/本地分派 → 取解 → 输出
# =============================================================================
render("FLOW_MAIN", "主流程：建模 → 分派 → 求解 → 取解 → 输出",
       "导出层调用约定（REPORT §5）与启动/分派（§6）；地址为 RVA",
       [
           ("a", 0, 0, "start", [("建模：LaunchingOrder", 0), ("NewLaunchingOrder 0x14620", 1)]),
           ("b", 0, 1, "proc", [("AddSheet / AddPart / AddHole / AddToolPath", 0),
                                ("0x15BF0 / 0x14D10 / 0x16420 / 0x12C60", 1)]),
           ("c", 0, 2, "proc", [("Set* 选项：共边 / 多割炬 / 剪切 / 行-管材 / 间隙 / 线程", 0),
                                ("只写 LaunchingOrder 字段，此处不生效", 1)]),
           ("d", 0, 3, "proc", [("Structure::CreateProblem 0x1EE50（15305 B）", 0),
                                ("所有字段的唯一读取/生效点", 1)]),
           ("e", 0, 4, "dec", [("cns_force_cloud", 0), ("置位？", 0)], 1, 72),
           ("f", 0, 5, "proc", [("LaunchLocalComputation 0x2AB0", 0),
                                ("强制云端时转发：cns1/cns2.optalog.com", 1)]),
           ("g", 1, 4, "proc", [("LaunchComputation 0x6100（云端）", 0),
                                ("PUT /pb/ 提交 · GET /sol/ 取解", 1)]),
           ("h", 1, 5, "dec", [("云端失败", 0), ("？", 0)], 1, 72),
           ("i", 0, 6, "proc", [("0x1E70 本地启动器（3135 B）", 0),
                                ("校验 Order → 读 Keys → 线程数/迭代数", 1)]),
           ("j", 0, 7, "proc", [("MultiEngine::Run", 0),
                                ("seed / nb_max_threads / 策略表 → AlgoParameters 0x4EC00", 1)]),
           ("k", 0, 8, "proc", [("Multi::Supervisor 0x2F860 → Supervisor::Run 0x827F0", 0),
                                ("按 StrategyDescriber 每策略一线程（见搜索流程图）", 1)]),
           ("l", 2, 5, "io", [("WaitNextSolution / WaitComputationTermination", 0),
                              ("GetSolution / GetNesting / GetFillRatio", 1)]),
           ("m", 2, 6, "io", [("GenerateDxfNesting 0xBF70 · HtmlSolutionReport", 0),
                              ("DeleteLaunchingOrder / AsyncCancelAll", 1)]),
       ],
       [
           ("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"),
           ("e", "g", "是"), ("e", "f", "否"),
           ("g", "h"), ("h", "l", "否"), ("h", "f", "是：回退本地"),
           ("f", "i"), ("i", "j"), ("j", "k"), ("k", "l"), ("l", "m"),
       ],
       ["注意：LaunchComputation ⇄ LaunchLocalComputation 互相调用 = 「云端不可用则本地算 / 强制云端」双向回退（已证实）。",
        "计算控制族（Wait*/Cancel*/Terminate*）都以 `cmp byte [rcx+0x48], 0` 起手，在日志里以 \"Local\"/\"Cloud\" 区分分支。"])

# =============================================================================
# 2. 多策略并发搜索
# =============================================================================
render("FLOW_SEARCH", "搜索：多策略并发 + 级联预算 + 观察者择优",
       "REPORT §7.2；时间闸门是唯一的全局总闸",
       [
           ("a", 0, 0, "start", [("Supervisor::Run 0x827F0", 0)]),
           ("b", 0, 1, "proc", [("AdvancedStrategist::operator() 0x2DF60", 0),
                                ("选 4 条路：mode 2 / 3 / 4 / 默认", 1)]),
           ("c", 0, 2, "proc", [("0x2CCF0 展开成 1–4 个预算递减变体", 0),
                                ("n → 2 → (n+1)/2 → n−1", 1)]),
           ("d", 0, 3, "dec", [("SupervisorCanceller::ProbeCancel 0x30030", 0),
                               ("elapsed / Problem[+0x408] > 1.0 ？", 0)], 1, 84),
           ("e", 0, 4, "proc", [("置粘滞标志 + __gthread_cond_broadcast", 0),
                                ("广播取消 → 所有策略线程收敛退出", 1)]),
           ("f", 1, 3, "proc", [("Nester::Prepare (v3) / Estimate (v4)", 0),
                                ("每个策略独立；NestingContextPool 复用上下文", 1)]),
           ("g", 1, 4, "proc", [("Nester::Run (v5)", 0),
                                ("每类最大的函数；见 Nester 流程图", 1)]),
           ("h", 1, 5, "proc", [("Observer::NewNestingFound", 0),
                                ("NewIntermediateSolutionFound 0x755A80 / 0x75CDA0", 1)]),
           ("i", 1, 6, "proc", [("BestObserver 择优", 0),
                                ("CompositeEngine 用 CompositeObserver 0x8D4500 聚合", 1)]),
           ("j", 0, 6, "note", [("并行取消器（各阶段独立）", 0),
                                ("Compact 0x7D2610 · NoFitMap 0x7D29F0 · Warp 0x7D7940", 1),
                                ("RCompact 0x7D2CB0 = xor eax,eax（旋转压缩阶段不可取消）", 1)], 1, 84),
           ("k", 2, 5, "end", [("返回最优解", 0)]),
       ],
       [
           ("a", "b"), ("b", "c"), ("c", "d"), ("d", "e", "超时"), ("d", "f", "未超时"),
           ("f", "g"), ("g", "h"), ("h", "i"), ("i", "k"),
       ],
       ["NestingNester 自带 std::mt19937（构造器 0x342E0：imul eax,eax,0x6C078965；[+0x9F8] = 0x270 = 624）",
        "⇒ 是「带随机扰动的确定性局部搜索」，不是遗传算法、也不是纯随机重启（已证实）。"])

# =============================================================================
# 3. Nester 内部（以 NestingNester 为例）
# =============================================================================
render("FLOW_NESTER", "Nester::Run 内部（以 Multi::NestingNester 0x378E0 为例）",
       "REPORT §7.2；14374 B 的主打包器",
       [
           ("a", 0, 0, "start", [("NestingNester::Run 0x378E0", 0)]),
           ("b", 0, 1, "proc", [("对象布局（由构造器证实）", 0),
                                ("+0x18/+0x20 mode/flags · +0x28 预算 · +0x30 比例(≥1.0)", 1),
                                ("+0x38..+0x9F8 MT19937 · +0xA00 PackerCache", 1)], 1, 84),
           ("c", 0, 2, "dec", [("enable_rectangle /", 0), ("force_rectangle ？", 0)], 1, 72),
           ("d", 1, 2, "proc", [("矩形快速路径 RectangleNester 0x75FB0", 0),
                                ("nb_rectangle_try · nb_iterations_before_rectangle_dual", 1)]),
           ("e", 0, 3, "proc", [("核心排布 A: 0x344D0（6748 B）", 0)]),
           ("f", 0, 4, "proc", [("核心排布 B: 0x35F30（6436 B）", 0)]),
           ("g", 0, 5, "proc", [("nesting_context.cpp: 0x3F070 / 0x434D0", 0)]),
           ("h", 0, 6, "proc", [("tiled_multipart.cpp: 0x185750 / 0x185A40 / 0x187020 / 0x189CA0", 0)]),
           ("i", 0, 7, "proc", [("beam 树准备 0x22CCA0（2916 B）", 0),
                                ("tree_db 0x1C1650 + 互斥锁 0x63F6C0/0x63F6B8", 1)]),
           ("j", 0, 8, "proc", [("节点评分（叶/内部）", 0),
                                ("TerminalNode 0x974F0 → [rcx+0x48] · SplitNode 0x97510 → +0x50", 1)]),
           ("k", 0, 9, "end", [("产出 nesting 候选 → 交给 Observer", 0)]),
       ],
       [
           ("a", "b"), ("b", "c"), ("c", "d", "是"), ("d", "e"),
           ("c", "e", "否"), ("e", "f"), ("f", "g"), ("g", "h"), ("h", "i"), ("i", "j"), ("j", "k"),
       ],
       ["beam width 的具体常量未找到（切入口：0x1C1650 的实现与 0x22CCA0 中 ebp 的来源）→ 未确认（已如实记录）。",
        "其它策略的 Run：Tiling 0x46940（16258 B，最大）· Compact 0xB13D0 · NoFill 0x7F240 · Database 0x5B250 …"])

# =============================================================================
# 4. NFP 计算链路
# =============================================================================
render("FLOW_NFP", "几何：No-Fit Polygon 计算链路（边界 Convolution）",
       "REPORT §7.1；极角归并完全不用 atan2，全部是 128 位精确谓词",
       [
           ("a", 0, 0, "start", [("GetNoFitMap 0x8AC0 / GetNoFitPlacementMap 0xA620", 0)]),
           ("b", 0, 1, "proc", [("0x665BF0 缓存「取或算」", 0)]),
           ("c", 0, 2, "dec", [("命中 NFPMap 缓存 ？", 0),
                               ("+0x78 / +0xA8 两个 map<Key(4×int64), vector<Polygon>>", 0)], 1, 84),
           ("d", 1, 2, "proc", [("直接返回缓存的多边形", 0)]),
           ("e", 0, 3, "proc", [("0x585CA0", 0),
                                ("ToExactPerimeter 0x6863C0（tol = 1e-6）× 2 → 定点化 ×1e10", 1)]),
           ("f", 0, 4, "proc", [("0x5A2530 → 0x5A11B0 → 0x59E9D0 \"NoFitMapWithoutHoles\"", 0),
                                ("→ 0x59CD10 → 0x59C560", 1)]),
           ("g", 0, 5, "proc", [("ConvolutionRaw 0x596F20（..\\exact\\convolution.cpp）", 0),
                                ("断言 max_size >= union(size1, size2)（行 331）", 1)]),
           ("h", 0, 6, "proc", [("核心 0x596100：0x595A80 生成 40 B 有向边", 0),
                                ("用 128 位叉积 0x58E450 判凸/凹", 1)]),
           ("i", 0, 7, "proc", [("0x596000 生成 64 B Edge 记录", 0),
                                ("{A@+0x00, B@+0x10, C@+0x20, bool, bool}", 1)]),
           ("j", 0, 8, "proc", [("主循环 0x596231–0x59631F：仅用 (dx,dy) 的符号分象限 1..4", 0),
                                ("1=(dx>0,dy>0) 2=(dx>0,dy≤0) 3=(dx≤0,dy<0) 4=其余", 1)]),
           ("k", 0, 9, "proc", [("按极角键输出 40 B 事件记录并归并", 0),
                                ("{tag, quadrant, dy, dx, ±1, flags, index} → [out+0x48]", 1)]),
           ("l", 0, 10, "proc", [("对同一对多边形调用两次并交换（r9d = 1 再 0）", 0),
                                 ("得到两个方向的 NFP", 1)]),
           ("m", 0, 11, "proc", [("0x687080 转回 double", 0)]),
           ("n", 0, 12, "dec", [("缓存总数 > 0x1312CFF", 0), ("（19,999,999）？", 0)], 1, 72),
           ("o", 1, 12, "proc", [("清空 NFPMap 缓存", 0)]),
           ("p", 0, 13, "end", [("返回 vector<Polygon>（NoFitGeometry 24 B）", 0)]),
       ],
       [
           ("a", "b"), ("b", "c"), ("c", "d", "是"), ("c", "e", "否"), ("d", "p"),
           ("e", "f"), ("f", "g"), ("g", "h"), ("h", "i"), ("i", "j"), ("j", "k"),
           ("k", "l"), ("l", "m"), ("m", "n"), ("n", "o", "是"), ("o", "p"), ("n", "p", "否"),
       ],
       ["复杂度上限 m_max_complexity 在 NoFitContext +0xE8，默认为 25000 = 0x61A8（NoFitSetMaximumComplexity 直写）。",
        "定位：算法结构（象限分类 + 事件归并 + 精确谓词）已证明；「等价于教科书式 edge-merge Minkowski 和」为推断。"])

# =============================================================================
# 5. 逐零件行排样 + 挤压代价
# =============================================================================
render("FLOW_ROW", "行排样：逐零件路径（候选角度 → 分值 → 取最小）",
       "findings_lp_use §21–§38；整条链已闭合，注入点为 0",
       [
           ("a", 0, 0, "start", [("0x134470 候选角度循环（bestCandidate）", 0)]),
           ("b", 0, 1, "proc", [("0x8BEFC0 + 0x5C4C50 构造候选集", 0),
                                ("源自带元素 + 0° + 90°（0x13450B 追加）", 1)]),
           ("c", 0, 2, "dec", [("0x5C2E40 授权谓词通过 ？", 0),
                               ("{tag, lo=角度, hi=角度}，两种区间极性", 0)], 1, 84),
           ("d", 0, 3, "proc", [("0x133DE0 逐零件代价", 0),
                                ("0x5CEE50 角度→变换（tag≠0 → 镜像 {cos,+sin,sin,−cos}）", 1)]),
           ("e", 0, 4, "proc", [("0x5D38C0 仿射变换 → 0x5CD800 包围盒", 0),
                                ("0x133E67 取 20 × 高（rodata 0x9BCEB0）", 1)]),
           ("f", 0, 5, "proc", [("构造：Item 0x1333D0（0x90）→ 元素 0x136350（216 B）", 0),
                                ("→ Row::Squeezer 0x136B80 / 0x138A20", 1)]),
           ("g", 0, 6, "proc", [("0x137FE0 排空源记录（每条最多重试 count = 10000）", 0),
                                ("→ 0x137A90 合并 → 虚调用 slot 1 = 0x13A360", 1)]),
           ("h", 0, 7, "proc", [("0x13A360 / 0x1380D0 记忆化挤压代价", 0),
                                ("阈值/sin − max(跨度)；1e-06 平行闸 + 0.005 对齐闸", 1)]),
           ("i", 0, 8, "proc", [("0x137800 orderedAddElement（+ 重置分值缓存 -1.0）", 0),
                                ("→ 0x136CB0 惰性分值 = nodeLength(末元素) + 末元素值", 1)]),
           ("j", 0, 9, "dec", [("分值 < 当前最优 ？", 0)], 1, 72),
           ("k", 1, 9, "proc", [("记住该候选（寄存器保存）", 0)]),
           ("l", 0, 10, "dec", [("还有候选元素 ？", 0)], 1, 72),
           ("m", 1, 10, "proc", [("取下一个候选角度", 0)]),
           ("n", 0, 11, "end", [("返回最小分值的角度（全被拒则返回 0）", 0)]),
       ],
       [
           ("a", "b"), ("b", "c"), ("c", "d", "是"), ("c", "m", "否"),
           ("d", "e"), ("e", "f"), ("f", "g"), ("g", "h"), ("h", "i"),
           ("i", "j"), ("j", "k", "是"), ("j", "l", "否"), ("k", "l"),
           ("l", "m", "是"), ("m", "c"), ("l", "n", "否"),
       ],
       ["最终公式（各端均已命名）：score = Squeezer::cost(上一条记录的 node, 当前元素) − 环形面积 / cfg[+0x08]",
        "元素（ScoreNode，216 B）的布局由 15 条 static_assert 锁进编译期；cfg[+0x08] = core+0x10 的配置系数。"])

# =============================================================================
# 6. Compaction 与收尾三连
# =============================================================================
render("FLOW_POSTOP", "后优化：Compaction + 收尾三连 pass",
       "REPORT §7.2（Compaction 与 0x1B33B0）",
       [
           ("a", 0, 0, "start", [("得到候选 nesting", 0)]),
           ("b", 0, 1, "proc", [("Compact::Compacter::Implementation v2 = 0x7F4140", 0),
                                ("取几何 → operator new(0x1E8) → 内核 0x252B60（1389 B）", 1)]),
           ("c", 0, 2, "proc", [("网格步长 = min(宽,高) / 10.0（常量 10.0 @ 0x9C2BB0）", 0),
                                ("构造区间 (-f1, 0, f1+f2) 的网格 → 0x5CA780 / 0x5C6BE0", 1)]),
           ("d", 0, 3, "proc", [("0x2664F0(obj+0x18, grid, 0, 1) 枚举网格 → 逐个候选 move", 0)]),
           ("e", 0, 4, "dec", [("RotateCompact 0x678230 接受测试", 0),
                               ("1e-6 > param ？（常量 0x9BF5D0）", 0)], 1, 84),
           ("f", 1, 4, "proc", [("直接放弃该次旋转（return 0）", 0)]),
           ("g", 0, 5, "proc", [("接受/拒绝；RCompact::RotateLogger 0xA533D0 只是日志钩子", 0)]),
           ("h", 0, 6, "proc", [("核心 0x1B33B0（9910 B）：USE_POSTOP / postop_estimate", 0)]),
           ("i", 0, 7, "proc", [("① postop.cpp 通用后处理", 0)]),
           ("j", 0, 8, "proc", [("② RenestInHoles 0x40720（Multi::HoleRenester）", 0),
                                ("把零件重新塞进已有 nesting 的孔洞（几何容差 1e-6）", 1)]),
           ("k", 0, 9, "proc", [("③ BL/BLF 稳定化 0x1E1BF0（packed bottom left）", 0),
                                ("不重叠前提下尽量推向左下 → 解规范化、便于去重比较", 1)]),
           ("l", 0, 10, "end", [("输出规范化后的解", 0)]),
       ],
       [
           ("a", "b"), ("b", "c"), ("c", "d"), ("d", "e"), ("e", "f", "是"),
           ("e", "g", "否"), ("f", "g"), ("g", "h"), ("h", "i"), ("i", "j"), ("j", "k"), ("k", "l"),
       ],
       ["参数键：enable_last_compaction / enable_rotate_compact_postop / nb_iterations_before_rotate_compact_postop。",
        "字符串证据：compacting ... · before_shake / shaker_ / after_shake（\"shake\" 抖动）· Swap Postop begin / Swap 180 begin。"])

# =============================================================================
# 7. LP / 定价层
# =============================================================================
render("FLOW_LP", "LP 与定价层（Prc / Lp / Coin）",
       "REPORT §7.3；这一层是活的（vtable 地址点被真实 lea 引用）",
       [
           ("a", 0, 0, "start", [("压缩/后优化路径进入定价器", 0),
                                 ("CompactNester::Run 0xB13D0 → 0xB0380 → 0x67460", 1)]),
           ("b", 0, 1, "proc", [("→ 0x1CD290 → 0x1CB100 → 0x1A6020 → 0x1A5B20", 0)]),
           ("c", 0, 2, "proc", [("定价器工厂 0x4D64C0", 0),
                                ("构造 Box / Hull / Alpha / LinearCombination 四个定价器", 1)]),
           ("d", 0, 3, "dec", [("哪个定价器 ？", 0)], 1, 72),
           ("e", 0, 4, "proc", [("Box: 主算法 0x7C9D90", 0),
                                ("面积 (y1−y0)*(x1−x0) @ 0x7CB750", 1)]),
           ("f", 1, 4, "proc", [("Hull: slot2 0x7CA130 = [rdx+0x48]", 0),
                                ("预置凸包面量系数", 1)]),
           ("g", 2, 4, "proc", [("Alpha: slot2 0x7CA1B0 = [rdx+0x68]", 0),
                                ("预置 α-shape 面量系数", 1)]),
           ("h", 3, 4, "proc", [("LinearCombination: slot2 0x7CA370", 0),
                                ("Σwᵢ·priceᵢ / Σwᵢ 加权平均", 1)]),
           ("i", 0, 5, "proc", [("PriceComputer 本体 0x7C4C70 / 0x7C4F90", 0),
                                ("[obj+0x10] 尾调用内部 +0x28/+0x30/+0x38/+0x40 槽", 1)]),
           ("j", 0, 6, "proc", [("Lp::LinearProgram ← Coin::CoinLP（vptr + ClpSimplex* @+8）", 0),
                                ("构造 0x267760；上下界/目标 ±inf、±1.0", 1)]),
           ("k", 0, 7, "proc", [("addColumn / addRow 装配 0x7CA830（3778 B）", 0),
                                ("对 16 B {double,int,int} 记录做有序插入/去重/扩容", 1)]),
           ("l", 0, 8, "proc", [("转发 thunk → ClpSimplex", 0),
                                ("0x7CB700→[+0x248] · 0x7CB710→[+0x228] · 0x7CB740→[+0x230]", 1)]),
           ("m", 0, 9, "end", [("取回原/对偶目标值", 0)]),
       ],
       [
           ("a", "b"), ("b", "c"), ("c", "d"),
           ("d", "e", "Box"), ("d", "f", "Hull"), ("d", "g", "Alpha"), ("d", "h", "Linear"),
           ("e", "i"), ("f", "i"), ("g", "i"), ("h", "i"),
           ("i", "j"), ("j", "k"), ("k", "l"), ("l", "m"),
       ],
       ["本层是否构成「列生成」尚未证实（findings_lp §7.3）；Prc::BoostAlpha / SurfaceCoeffs / DimAlpha 只有 RTTI 名、零指针引用。",
        "方法学提醒：搜 vtable 头部（vtable+0）会得到「0 引用」的假结论；vptr 指向的是地址点（vtable+16）。"])
print("charts written")
