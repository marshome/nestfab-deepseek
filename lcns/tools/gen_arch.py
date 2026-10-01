# -*- coding: utf-8 -*-
"""Generate docs/ARCHITECTURE.svg (layered architecture) and docs/ROW_PATH.svg (the per-part path).

Run:  python tools/gen_arch.py
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "docs")

FONT = "font-family=\"Segoe UI, Microsoft YaHei, Noto Sans CJK SC, sans-serif\""
MONO = "font-family=\"Cascadia Mono, Consolas, monospace\""

C_DLL = "#1f3a5f"      # dll column header
C_DLLF = "#eef4fb"
C_LC = "#1f4d3a"       # lcns column header
C_LCF = "#eefaf3"
C_LINE = "#8899aa"
C_ACC = "#b45309"      # accent for the closed path


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def box(x, y, w, h, fill, stroke, lines, r=6, title_size=13, body_size=11, mono=False):
    out = ['<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s" stroke="%s" '
           'stroke-width="1.2"/>' % (x, y, w, h, r, fill, stroke)]
    ty = y + 18
    for i, (txt, kind) in enumerate(lines):
        if kind == "t":
            out.append('<text x="%d" y="%d" %s font-size="%d" font-weight="600" fill="%s">%s</text>'
                       % (x + 10, ty, FONT, title_size, stroke, esc(txt)))
            ty += title_size + 5
        else:
            fam = MONO if mono else FONT
            out.append('<text x="%d" y="%d" %s font-size="%d" fill="#33404d">%s</text>'
                       % (x + 10, ty, fam, body_size, esc(txt)))
            ty += body_size + 4
    return "\n".join(out)


def arrow(x1, y1, x2, y2, color=C_LINE, dash=None, width=1.2, marker="arrow"):
    d = ' stroke-dasharray="5,4"' if dash else ''
    return ('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%.1f"%s '
            'marker-end="url(#%s)"/>' % (x1, y1, x2, y2, color, width, d, marker))


def gen_layered():
    L, C1, C2 = 40, 300, 900          # label column, dll column, lcns column
    CW = 560                          # column width
    rows = [
        ("导出 / API 层",
         [("t", "168 个唯一函数 / 336 个导出项"), ("b", "全部按序号导出，NumberOfNames = 0"),
          ("b", "162/168 名字由 dbg::symlog 实参恢复")],
         [("t", "lcns::dll::Library / Api"), ("b", "include/lcns/api.hpp  src/api.cpp"),
          ("b", "detail/api_table.inc + api_typed.inc（由 re/ 生成）"),
          ("b", "lcns_probe：按序号探测真实 DLL")]),
        ("引擎 / 调度层",
         [("t", "Nest::Supervisor / Nest::Engine"), ("b", "Supervisor::Run 0x827F0"),
          ("b", "beam search 0x22CCA0；级联 0x2CCF0"),
          ("b", "取消闸 elapsed / Problem[+0x408] > 1.0")],
         [("t", "lcns::Supervisor / lcns::Engine"), ("b", "src/engine.cpp  src/nester.cpp"),
          ("b", "Random / Canceller / TimeCanceller"),
          ("b", "Observers / BestObserver")]),
        ("策略层（12 个 Nester）",
         [("t", "Multi::*Nester（各自 Run 槽）"), ("b", "Nesting 0xA3B690/Run 0x378E0  Flip 0x4B870"),
          ("b", "Filter 0xB3AE0  NoFill 0x7F240  Tiling 0x46940"),
          ("b", "Compact 0xB13D0  Limited 0x4AB40  Database 0x5B250"),
          ("b", "Rectangle 0x75FB0  Row 0x913E0  MultiTorch 0x7BCC0"),
          ("b", "Composite 0xA3B780（壳）")],
         [("t", "lcns::*Nester（12 个同名类）"), ("b", "include/lcns/nester.hpp"),
          ("b", "pack::BestNester / KnapsackNester / RecursiveNester"),
          ("b", "每个类注释保留其 vtable AP 与 Run 地址")]),
        ("行排样核心（逐零件路径）",
         [("t", "Multi::RowNester + Row::Squeezer"), ("b", "RowNester AP 0xA3BB40 ctor 0x8F210 Run 0x913E0"),
          ("b", "core 0xD0：0x6AABC0 → new；core+0xC0 = Squeezer"),
          ("b", "Squeezer ctor 0x138A20  cost 0x1380D0 / 0x13A360"),
          ("b", "逐零件：0x134470 → 0x133DE0 → 0x136350"),
          ("b", "→ 0x137FE0 → 0x137A90 → 0x137800 → 0x136CB0")],
         [("t", "lcns::RowNester / RowNestCore / row::Squeezer"), ("b", "include/lcns/row.hpp (941 行)  src/row.cpp"),
          ("b", "row::bestCandidate / chainMonotone / dllArea"),
          ("b", "row::orderedAddElement / candidateScore / LazyScorer"),
          ("b", "tests/test_row.cpp (693 行) —— 15 条 static_assert 锁定元素布局")]),
        ("几何内核（全自研）",
         [("t", "..\\\\exact\\\\* + ..\\\\geom\\\\*"), ("b", "exact：int64 定点，scale 1e10，128 位行列式谓词"),
          ("b", "geom：double；Geom::MultiPolygon / PolygonProxy"),
          ("b", "NFP = 边界 Convolution；NoFitMap 缓存"),
          ("b", "无 Clipper / boost::geometry / CGAL / Eigen")],
         [("t", "lcns::geom"), ("b", "src/geom.cpp (729)  src/boolean.cpp (602)"),
          ("b", "Int128 / mul64 / orient2d / kScale = 1e10"),
          ("b", "minkowskiSum / nfp / offsetOnce / inflatePolygon"),
          ("b", "src/nfp.cpp：NoFitMap / forbiddenRegion")]),
        ("LP / 定价层",
         [("t", "Lp::LinearProgram / Coin::CoinLP"), ("b", "Clp 1.15.3 + CoinUtils 静态链接"),
          ("b", "Prc::PriceComputer：Box/Hull/Alpha/LinearCombination"),
          ("b", "AP 0xA3B0C0 / 0xA3B100 / 0xA3B140 / 0xA3B180"),
          ("b", "OR-Tools：13 个标记全 0 命中")],
         [("t", "lcns::lp::LinearProgram / Simplex"), ("b", "src/lp.cpp (590)  src/lp_nesting.cpp"),
          ("b", "零依赖自研 Simplex（本机无 Clp，已如实记录）"),
          ("b", "lp_column_generation.*：隔离区，标注 NOT PART OF THE BINARY")]),
        ("切割工艺特性",
         [("t", "共边 / 多割炬 / 剪切 / 管材-行模式"), ("b", "SetCommonCutParameters 0x3C3F0"),
          ("b", "  → Pb+0x188..+0x1C8 结构拷贝（0x185A40）"),
          ("b", "SetPipeMode 0xFCF0 → Pb+0x170"),
          ("b", "皮革/纹理、缺陷区、余料")],
         [("t", "lcns::Order 的工艺字段 + 共边检测"), ("b", "model.hpp：pipeMode / cfgAt1xx / commonCut*"),
          ("b", "nester.cpp：detectCommonCuts / compactNesting"),
          ("b", "io.cpp：offcuts；round-trip 保留 pipe_enable")]),
        ("云端 / 许可",
         [("t", "Sentinel HASP / Admin API + HTTP"), ("b", "运行期 LoadLibraryA 载入 Sentinel"),
          ("b", "CryptoPP 整库静态链接，授权路径未见调用点"),
          ("b", "机器绑定：MAC + 卷序列号")],
         [("t", "lcns::cloud / lcns::licensing"), ("b", "src/cloud.cpp (384)  src/licensing.cpp (287)"),
          ("b", "computePcid = ((mac32*vol)+mac16+mac32+vol) ^ 0xABADCAFE"),
          ("b", "vendor code 刻意未内嵌")]),
    ]
    y = 100
    rh = 118
    total_h = 100 + len(rows) * (rh + 16) + 6 + 72 + 24      # computed, never clipped
    W = 1500
    H = total_h
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d">' % (W, H, W, H),
             '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
             'markerHeight="7" orient="auto-start-reverse">'
             '<path d="M 0 0 L 10 5 L 0 10 z" fill="%s"/></marker>'
             '<marker id="arrow2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
             'markerHeight="7" orient="auto-start-reverse">'
             '<path d="M 0 0 L 10 5 L 0 10 z" fill="%s"/></marker></defs>' % (C_LINE, C_ACC),
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             '<text x="%d" y="42" %s font-size="26" font-weight="700" fill="#10202f">'
             'liblcns.dll 逆向架构  ×  lcns 等价重建工程</text>' % (L, FONT),
             '<text x="%d" y="70" %s font-size="13" fill="#55636f">'
             '左侧＝后端恢复出的真实类型与地址（RVA，ImageBase 0x6B4C0000）；右侧＝lcns 工程中的对应实现</text>'
             % (L, FONT),
             '<text x="%d" y="92" %s font-size="14" font-weight="700" fill="%s">DLL（已恢复）</text>'
             % (C1, FONT, C_DLL),
             '<text x="%d" y="92" %s font-size="14" font-weight="700" fill="%s">lcns（重建）</text>'
             % (C2, FONT, C_LC)]

    for i, (label, dll_lines, lc_lines) in enumerate(rows):
        # layer label
        parts.append('<text x="%d" y="%d" %s font-size="12.5" font-weight="600" fill="#33404d">%s</text>'
                     % (L, y + rh // 2, FONT, esc(label)))
        parts.append(box(C1, y, CW, rh, C_DLLF, C_DLL, dll_lines, mono=True))
        parts.append(box(C2, y, CW, rh, C_LCF, C_LC, lc_lines))
        # mapping arrow (same layer)
        parts.append(arrow(C1 + CW + 4, y + rh // 2, C2 - 6, y + rh // 2, C_ACC, dash="5,4", marker="arrow2"))
        # dependency arrows inside each column: lower layers are depended upon (upward)
        if i + 1 < len(rows):
            ny = y + rh
            parts.append(arrow(C1 + CW // 2, ny + 16, C1 + CW // 2, ny + 6, C_DLL, width=1.0))
            parts.append(arrow(C2 + CW // 2, ny + 16, C2 + CW // 2, ny + 6, C_LC, width=1.0))
        y += rh + 16

    y += 6
    parts.append('<rect x="%d" y="%d" width="%d" height="72" rx="6" fill="#fff8ec" stroke="%s" '
                 'stroke-width="1.2" stroke-dasharray="6,4"/>' % (C1, y, CW * 2 + 40, C_ACC))
    parts.append('<text x="%d" y="%d" %s font-size="13" font-weight="600" fill="%s">'
                 '可追溯性闭环</text>' % (C1 + 12, y + 20, FONT, C_ACC))
    parts.append('<text x="%d" y="%d" %s font-size="11.5" fill="#33404d">'
                 '每个常量/函数在代码注释里带 RVA  →  re/g_acceptance.py 校验「文档 ↔ 代码 ↔ 地址」三方一致（108/108）'
                 '</text>' % (C1 + 12, y + 40, FONT))
    parts.append('<text x="%d" y="%d" %s font-size="11.5" fill="#33404d">'
                 're/g_final_check.py 复核 22 个逆出原语均在工程中；零警告构建 32 TU；ctest 15/15</text>'
                 % (C1 + 12, y + 58, FONT))
    parts.append('</svg>')
    io.open(os.path.join(OUT, "ARCHITECTURE.svg"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(parts))
    print("wrote ARCHITECTURE.svg")


def gen_row_path():
    W = 1500
    steps = [
        ("0x134470", "候选角度循环", "取最小（ucomisd/jbe）；谓词不过则跳过", "#fff8ec", C_ACC),
        ("0x8BEFC0 / 0x5C4C50", "候选集 = 源自带 + 0° + 90°",
         "0x5C4C50 只有 4 条指令：写 {tag@+0, angle@+8}；0x13450B 追加 90°", C_LCF, C_LC),
        ("0x5C2E40", "授权谓词（角度区间）", "记录 0x5C4950 建：{tag, lo=角度, hi=角度}；两种区间极性", C_LCF, C_LC),
        ("0x133DE0", "逐零件代价（入口）", "包围盒 → 20 × 高 → Item → Squeezer", C_LCF, C_LC),
        ("0x1333D0", "Item 构造（0x90）", "vector<Elem48>@+0x08；两个 vector<Elem216>@+0x58/+0x70", C_LCF, C_LC),
        ("0x136350", "216 字节元素构造", "15 条 static_assert 锁定 ScoreNode 逐偏移；+0x08/+0x10 = 产生它的候选记录", C_LCF, C_LC),
        ("0x1355C0 / 0x5D3430", "元素自己的几何步", "用自己的角度变换 + 平移到原点（xorpd -0.0）", C_LCF, C_LC),
        ("0x134D70", "两个标志 +0x40 / +0x41", "闭合点链（16 字节 Elem16）的单调谓词；1e-06 + fabs 掩码", C_LCF, C_LC),
        ("0x136B80 / 0x138A20", "Row::Squeezer 构造", "(20×高, cfg[+0x18], cfg[+0x10])", C_LCF, C_LC),
        ("0x137FE0", "排空源记录", "每条记录最多重试 count=10000 次（0x271000000000 的 u32@+0xc）", C_LCF, C_LC),
        ("0x137A90", "合并 → 代价", "slot 1 = 0x13A360 = Squeezer::cost(上一条记录的 node, 当前元素)", C_LCF, C_LC),
        ("0x13A360 / 0x1380D0", "记忆化挤压代价", "cost = 阈值/sin − max(跨度)；1e-06 平行闸 + 0.005 对齐闸", C_LCF, C_LC),
        ("0x137800", "orderedAddElement", "追加 16 字节 {node*, double}（步长 0x10）并重置分值缓存", C_LCF, C_LC),
        ("0x136CB0", "惰性分值（返回值）", "末元素决定：nodeLength(末) + 末值；缓存哨兵 -1.0", "#fff8ec", C_ACC),
    ]
    y0, rh, gap = 108, 74, 16
    H = y0 + len(steps) * (rh + gap) + 24          # computed, never clipped
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
             % (W, H, W, H),
             '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
             'markerHeight="7" orient="auto-start-reverse">'
             '<path d="M 0 0 L 10 5 L 0 10 z" fill="%s"/></marker></defs>' % C_LINE,
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             '<text x="40" y="42" %s font-size="24" font-weight="700" fill="#10202f">'
             '逐零件路径（已闭合）：从候选角度到最终分值</text>' % FONT,
             '<text x="40" y="70" %s font-size="13" fill="#55636f">'
             '每个框的左列是 RVA；右侧为语义。橙色框＝该路径的入口与出口。</text>' % FONT,
             '<text x="40" y="94" %s font-size="12" fill="#8899aa">'
             'score = Squeezer::cost(上一条记录, 当前元素) − 环形面积 / cfg[+0x08]</text>' % FONT]
    y = y0
    for i, (addr, title, sub, fill, stroke) in enumerate(steps):
        parts.append(box(60, y, 1380, rh, fill, stroke,
                         [("t", title), ("b", sub)], title_size=14, body_size=11))
        parts.append('<text x="72" y="%d" %s font-size="12" font-weight="700" fill="%s">%s</text>'
                     % (y + rh - 10, MONO, stroke, esc(addr)))
        if i + 1 < len(steps):
            parts.append(arrow(750, y + rh + 2, 750, y + rh + gap - 2))
        y += rh + gap
    parts.append('</svg>')
    io.open(os.path.join(OUT, "ROW_PATH.svg"), "w", encoding="utf-8", newline="\n").write(
        "\n".join(parts))
    print("wrote ROW_PATH.svg (height %d)" % (y + 20))


gen_layered()
gen_row_path()

# --- validate: must be well-formed XML with the expected canvas -----------------
import xml.etree.ElementTree as ET

for name in ("ARCHITECTURE.svg", "ROW_PATH.svg"):
    p = os.path.join(OUT, name)
    root = ET.parse(p).getroot()
    kids = len(list(root))
    print("%-18s ok  %sx%s  elements=%d" % (name, root.get("width"), root.get("height"), kids))
