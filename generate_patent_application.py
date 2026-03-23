#!/usr/bin/env python3
"""Generate patent application PDF with claim design-around analysis."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Font ---
FONT = "SimSun"
font_paths = [
    ("SimSun", r"C:\Windows\Fonts\simsun.ttc"),
    ("SimSun", r"C:\Windows\Fonts\simsun.ttf"),
    ("SimHei", r"C:\Windows\Fonts\simhei.ttf"),
    ("Microsoft YaHei", r"C:\Windows\Fonts\msyh.ttc"),
]
for name, path in font_paths:
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            FONT = name
            break
        except:
            pass

# --- Colors ---
PRIMARY = HexColor("#1a365d")
SECONDARY = HexColor("#2b6cb0")
ACCENT = HexColor("#3182ce")
LIGHT_BG = HexColor("#ebf8ff")
BORDER = HexColor("#bee3f8")
HDR_BG = HexColor("#1a365d")
ROW_ALT = HexColor("#f7fafc")
RED_BG = HexColor("#fff5f5")
RED_BORDER = HexColor("#fc8181")
GREEN_BG = HexColor("#f0fff4")
GREEN_BORDER = HexColor("#68d391")
ORANGE_BG = HexColor("#fffaf0")
YELLOW_BG = HexColor("#fffff0")
GRAY = HexColor("#718096")

W = A4[0] - 40*mm  # usable page width

# --- Styles ---
S = {}
def _s(name, **kw):
    kw.setdefault("fontName", FONT)
    kw.setdefault("leading", kw.get("fontSize", 10) * 1.5)
    S[name] = ParagraphStyle(name, **kw)

_s("cover_title", fontSize=26, textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=6*mm)
_s("cover_sub", fontSize=13, textColor=SECONDARY, alignment=TA_CENTER, spaceAfter=4*mm)
_s("cover_info", fontSize=10, textColor=GRAY, alignment=TA_CENTER, spaceAfter=2*mm)
_s("h1", fontSize=17, textColor=PRIMARY, spaceBefore=8*mm, spaceAfter=5*mm)
_s("h2", fontSize=13, textColor=SECONDARY, spaceBefore=5*mm, spaceAfter=3*mm)
_s("h3", fontSize=11, textColor=ACCENT, spaceBefore=3*mm, spaceAfter=2*mm)
_s("body", fontSize=10, textColor=black, alignment=TA_JUSTIFY, spaceAfter=3*mm)
_s("body_indent", fontSize=10, textColor=black, alignment=TA_JUSTIFY, spaceAfter=2*mm, leftIndent=10)
_s("claim", fontSize=10, textColor=HexColor("#2d3748"), spaceAfter=2*mm, leftIndent=15, leading=16)
_s("claim_bold", fontSize=10, textColor=PRIMARY, spaceAfter=2*mm, leftIndent=15, leading=16)
_s("th", fontSize=9, textColor=white, alignment=TA_CENTER)
_s("tc", fontSize=8.5, textColor=HexColor("#2d3748"), alignment=TA_LEFT, leading=13)
_s("tc_c", fontSize=8.5, textColor=HexColor("#2d3748"), alignment=TA_CENTER, leading=13)
_s("small", fontSize=8, textColor=GRAY, alignment=TA_CENTER)
_s("red_box", fontSize=10, textColor=HexColor("#c53030"), spaceAfter=2*mm, leftIndent=10, leading=15)
_s("green_box", fontSize=10, textColor=HexColor("#276749"), spaceAfter=2*mm, leftIndent=10, leading=15)

def hcell(t): return Paragraph(t, S["th"])
def cell(t, c=False): return Paragraph(t, S["tc_c"] if c else S["tc"])
def divider():
    t = Table([[""]], colWidths=[W])
    t.setStyle(TableStyle([("LINEBELOW",(0,0),(-1,-1),1,BORDER),("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    return t

def colored_box(text, bg, border_color, style_name="body"):
    data = [[Paragraph(text, S[style_name])]]
    t = Table(data, colWidths=[W - 4*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), bg),
        ("BOX",(0,0),(-1,-1), 1, border_color),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("RIGHTPADDING",(0,0),(-1,-1),8),
    ]))
    return t


def build():
    doc = SimpleDocTemplate(
        r"D:\Code\pattren\patent_application_draft.pdf",
        pagesize=A4, leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )
    story = []

    # =========================================================
    # COVER
    # =========================================================
    story.append(Spacer(1, 35*mm))
    story.append(Paragraph("发明专利申请书（草案）", S["cover_title"]))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("一种半导体引线框的多层梯度镀覆方法及引线框结构", S["cover_sub"]))
    story.append(Spacer(1, 8*mm))

    cover_lines = [
        "技术领域：半导体封装 — 引线框表面处理",
        "规避对象：CN1770440A（Samsung Techwin，已过期）",
        "策略：基底材料替换 + 镀层结构创新 + 工艺参数差异化",
        "文件类型：发明专利申请（草案）",
        "生成日期：2026 年 3 月 23 日",
    ]
    for line in cover_lines:
        story.append(Paragraph(line, S["cover_info"]))

    story.append(Spacer(1, 15*mm))
    story.append(colored_box(
        "重要声明：CN1770440A 已于 2025 年 9 月 29 日届满过期，其技术方案可自由实施。"
        "本申请书的规避设计同时构成技术改进与创新，可独立申请新专利保护。",
        YELLOW_BG, HexColor("#d69e2e"), "body"
    ))

    story.append(PageBreak())

    # =========================================================
    # PART A: CLAIM DESIGN-AROUND ANALYSIS
    # =========================================================
    story.append(Paragraph("第一部分：原专利权利要求规避分析", S["h1"]))
    story.append(divider())

    story.append(Paragraph(
        "以下逐项分析 CN1770440A 的 19 项权利要求，说明本申请对每项主张的规避策略及修改依据。",
        S["body"]
    ))

    # ---- Group 1: Product claims 1-5 ----
    story.append(Paragraph("A. 产品权利要求（引线框）— 第 1-5 项", S["h2"]))

    g1_data = [
        [hcell("原权利要求"), hcell("核心限定"), hcell("规避策略"), hcell("本申请对应方案")],

        [cell("1. 半导体引线框：\nFe-Ni 合金基底 +\n晶粒 <1μm 镀层"),
         cell("(a) Fe-Ni 合金\n(b) 晶粒 <1μm\n(c) 单层镀层"),
         cell("(a) 改用铜合金基底\n(b) 采用多层梯度结构\n    替代单一晶粒控制\n(c) 引入中间阻挡层"),
         cell("铜合金基底 +\nNi 阻挡层 +\nSn-In 梯度镀层\n（三层结构）")],

        [cell("2. 镀层为 Sn 层"),
         cell("纯 Sn 镀层"),
         cell("使用 Sn-In 合金\n（铟不在原专利列举范围）"),
         cell("Sn-In 合金镀层\n（In 含量 3-8 wt%）")],

        [cell("3. 镀层为 Sn 合金层"),
         cell("Sn 合金层"),
         cell("合金体系差异化\n+多层结构差异化"),
         cell("三层梯度结构中的\nSn-In 合金外层")],

        [cell("4. Sn 合金含\nAg/Bi/Cu/Zn"),
         cell("合金元素限于\nAg、Bi、Cu、Zn"),
         cell("使用 In（铟）和/或\nSb（锑）、Ge（锗）\n均不在原专利列举范围"),
         cell("Sn-In 体系\n可选添加 Sb/Ge")],

        [cell("5. 合金金属\n含量 <5 wt%"),
         cell("添加金属 <5%"),
         cell("In 含量设定为\n3-8 wt%\n（跨越 5% 界限）"),
         cell("In: 3-8 wt%\nSb: 0-2 wt%\n总合金 3-10 wt%")],
    ]
    t = Table(g1_data, colWidths=[35*mm, 30*mm, 38*mm, 38*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), HDR_BG),
        ("GRID",(0,0),(-1,-1), 0.5, BORDER),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("BACKGROUND",(0,1),(0,-1), LIGHT_BG),
        ("BACKGROUND",(1,2),(-1,2), ROW_ALT),
        ("BACKGROUND",(1,4),(-1,4), ROW_ALT),
    ]))
    story.append(t)
    story.append(Spacer(1, 3*mm))

    story.append(colored_box(
        "规避要点：原独立权利要求 1 限定了「Fe-Ni 合金基底」+「晶粒 <1μm 的（单层）镀层」两个必要技术特征。"
        "本申请同时替换基底材料（铜合金）和镀层结构（三层梯度），从根本上脱离原权利要求的保护范围。"
        "此外，合金体系由 Sn-(Ag/Bi/Cu/Zn) 变更为 Sn-In，不落入从属权利要求 2-5 的限定。",
        GREEN_BG, GREEN_BORDER, "green_box"
    ))

    # ---- Group 2: Package claims 6-12 ----
    story.append(Paragraph("B. 产品权利要求（封装体）— 第 6-12 项", S["h2"]))

    g2_data = [
        [hcell("原权利要求"), hcell("核心限定"), hcell("规避策略"), hcell("本申请对应方案")],

        [cell("6. 半导体封装：\n外部连接引线上\n晶粒 <1μm 镀层"),
         cell("暴露表面上的\n晶粒 <1μm 镀层"),
         cell("多层梯度镀层替代\n单层晶粒控制"),
         cell("Ni 阻挡层 + Sn-In\n梯度过渡层 + Sn-In\n表面层的三层结构")],

        [cell("7. 引线由\nFe-Ni 合金形成"),
         cell("Fe-Ni 合金"),
         cell("改用铜合金引线框"),
         cell("C194 / C7025\n铜合金引线框")],

        [cell("8-11. 镀层为\nSn/Sn合金/含\nAg,Bi,Cu,Zn/<5%"),
         cell("同第 2-5 项"),
         cell("同 A 组策略"),
         cell("Sn-In 合金\n（In: 3-8 wt%）")],

        [cell("12. 引线外表面\n有 Ag 镀层"),
         cell("Ag 镀层"),
         cell("使用 Ni 阻挡层\n替代 Ag 镀层"),
         cell("Ni 阻挡层\n（0.5-2.0μm）")],
    ]
    t = Table(g2_data, colWidths=[35*mm, 30*mm, 38*mm, 38*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), HDR_BG),
        ("GRID",(0,0),(-1,-1), 0.5, BORDER),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("BACKGROUND",(0,1),(0,-1), LIGHT_BG),
        ("BACKGROUND",(1,2),(-1,2), ROW_ALT),
        ("BACKGROUND",(1,4),(-1,4), ROW_ALT),
    ]))
    story.append(t)

    story.append(PageBreak())

    # ---- Group 3: Method claims 13-19 ----
    story.append(Paragraph("C. 方法权利要求（电镀工艺）— 第 13-19 项", S["h2"]))

    g3_data = [
        [hcell("原权利要求"), hcell("核心限定"), hcell("规避策略"), hcell("本申请对应方案")],

        [cell("13. 方法：Fe-Ni 基底\n+ 晶粒 <1μm\nSn/Sn合金镀层"),
         cell("(a) Fe-Ni 基底\n(b) 单层镀覆\n(c) 晶粒 <1μm"),
         cell("(a) 铜合金基底\n(b) 三步分层镀覆\n(c) 应力梯度控制\n    替代晶粒控制"),
         cell("脉冲电镀法：\n第一步镀 Ni 阻挡层\n第二步镀 Sn-In 过渡层\n第三步镀 Sn-In 表面层")],

        [cell("14. 电流密度\n≥30 ASD"),
         cell("直流 ≥30 ASD"),
         cell("采用脉冲电镀\n平均电流密度\n15-25 ASD"),
         cell("脉冲电镀：\n峰值 40-60 ASD\n占空比 30-50%\n平均 15-25 ASD")],

        [cell("15-16. 高速喷嘴\n喷涂 >1 m/s"),
         cell("喷嘴喷涂方式\n速度 >1 m/s"),
         cell("采用超声波辅助\n搅拌替代喷嘴"),
         cell("超声波辅助搅拌\n频率 20-40 kHz\n无需高速喷嘴")],

        [cell("17. 方法：部分镀覆\n+ 冲洗完成"),
         cell("部分镀覆 +\n冲洗完成"),
         cell("全面镀覆 +\n选择性蚀刻"),
         cell("全面三层镀覆后\n选择性激光蚀刻\n去除非功能区域")],

        [cell("18-19. 刮平层\n~0.2μm + 剥除"),
         cell("Sn 刮平层\n0.2μm"),
         cell("Ni 阻挡层替代\nSn 刮平层"),
         cell("Ni 阻挡层\n0.5-2.0μm\n（功能与厚度均不同）")],
    ]
    t = Table(g3_data, colWidths=[35*mm, 30*mm, 38*mm, 38*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), HDR_BG),
        ("GRID",(0,0),(-1,-1), 0.5, BORDER),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("BACKGROUND",(0,1),(0,-1), LIGHT_BG),
        ("BACKGROUND",(1,2),(-1,2), ROW_ALT),
        ("BACKGROUND",(1,4),(-1,4), ROW_ALT),
    ]))
    story.append(t)
    story.append(Spacer(1, 3*mm))

    story.append(colored_box(
        "规避要点：原方法权利要求的三大核心限定为「Fe-Ni 基底」「直流高电流密度 ≥30ASD」「高速喷嘴 >1m/s」。"
        "本申请同时替换为「铜合金基底」「脉冲电镀（平均 15-25 ASD）」「超声波辅助搅拌」，"
        "三项必要技术特征均不落入原权利要求范围。",
        GREEN_BG, GREEN_BORDER, "green_box"
    ))

    # ---- Summary table ----
    story.append(Paragraph("D. 规避策略总览", S["h2"]))

    sum_data = [
        [hcell("原专利特征"), hcell("本申请替代方案"), hcell("规避类型")],
        [cell("Fe-Ni 合金（42 号）基底"), cell("铜合金（C194/C7025）基底"), cell("材料替换", True)],
        [cell("晶粒尺寸 <1μm 单层镀层"), cell("三层梯度镀层（Ni + Sn-In 过渡 + Sn-In 表面）"), cell("结构创新", True)],
        [cell("Sn 或 Sn-(Ag/Bi/Cu/Zn) 合金"), cell("Sn-In 合金（可选添加 Sb/Ge）"), cell("合金替换", True)],
        [cell("合金添加金属 <5 wt%"), cell("In 含量 3-8 wt%，总合金 3-10 wt%"), cell("参数差异", True)],
        [cell("直流电镀 ≥30 ASD"), cell("脉冲电镀，平均 15-25 ASD"), cell("工艺替换", True)],
        [cell("高速喷嘴搅拌 >1 m/s"), cell("超声波辅助搅拌（20-40 kHz）"), cell("工艺替换", True)],
        [cell("Sn 刮平层 ~0.2μm"), cell("Ni 阻挡层 0.5-2.0μm"), cell("功能替换", True)],
        [cell("Ag 外层镀覆"), cell("Ni 阻挡层（兼防扩散功能）"), cell("功能替换", True)],
    ]
    t = Table(sum_data, colWidths=[50*mm, 65*mm, 30*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), HDR_BG),
        ("GRID",(0,0),(-1,-1), 0.5, BORDER),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),5),
        ("RIGHTPADDING",(0,0),(-1,-1),5),
        ("BACKGROUND",(0,1),(0,-1), RED_BG),
        ("BACKGROUND",(1,1),(1,-1), GREEN_BG),
        ("BACKGROUND",(1,2),(-1,2), ROW_ALT),
        ("BACKGROUND",(1,4),(-1,4), ROW_ALT),
        ("BACKGROUND",(1,6),(-1,6), ROW_ALT),
        ("BACKGROUND",(1,8),(-1,8), ROW_ALT),
    ]))
    story.append(t)

    story.append(PageBreak())

    # =========================================================
    # PART B: PATENT APPLICATION DRAFT
    # =========================================================
    story.append(Paragraph("第二部分：发明专利申请书（草案）", S["h1"]))
    story.append(divider())

    # ---- Title ----
    story.append(Paragraph("【发明名称】", S["h2"]))
    story.append(Paragraph(
        "一种半导体引线框的多层梯度镀覆方法及引线框结构", S["body"]
    ))

    # ---- Field ----
    story.append(Paragraph("【技术领域】", S["h2"]))
    story.append(Paragraph(
        "本发明涉及半导体封装技术领域，具体涉及一种用于半导体引线框的多层梯度镀覆方法，"
        "以及采用该方法制备的半导体引线框结构和半导体封装体。本发明特别适用于需要高可靠性、"
        "抗晶须生长和良好焊接浸润性的半导体封装应用场景。",
        S["body"]
    ))

    # ---- Background ----
    story.append(Paragraph("【背景技术】", S["h2"]))
    story.append(Paragraph(
        "半导体引线框作为芯片与外部电路之间的电气连接载体，其表面镀层质量直接影响封装产品的可靠性。"
        "在无铅化趋势下，锡（Sn）及锡合金镀层被广泛应用于引线框表面，但锡镀层存在晶须（Whisker）"
        "生长的风险，可能导致短路或断路等严重失效。",
        S["body"]
    ))
    story.append(Paragraph(
        "现有技术中，通过控制镀层晶粒尺寸来抑制晶须的方法（如 CN1770440A）存在以下不足：\n"
        "（1）仅依赖单层镀层的晶粒尺寸控制，对基底与镀层界面的热应力问题缺乏系统解决；\n"
        "（2）要求使用特定的 Fe-Ni 合金基底，限制了材料选择的灵活性；\n"
        "（3）高电流密度直流电镀工艺对设备要求高，镀层均匀性受喷嘴分布影响较大；\n"
        "（4）Sn-(Ag/Bi/Cu/Zn) 合金体系的热膨胀匹配性仍有改善空间。",
        S["body"]
    ))
    story.append(Paragraph(
        "因此，需要一种既能有效抑制晶须生长，又能提供更好的界面应力管理和工艺灵活性的引线框镀覆技术。",
        S["body"]
    ))

    # ---- Technical Problem ----
    story.append(Paragraph("【发明内容】", S["h2"]))
    story.append(Paragraph("一、要解决的技术问题", S["h3"]))
    story.append(Paragraph(
        "本发明要解决的技术问题是：如何在铜合金引线框基底上形成具有优异抗晶须性能、"
        "良好焊接浸润性和界面可靠性的表面镀层，同时降低对电镀设备的特殊要求。",
        S["body"]
    ))

    story.append(Paragraph("二、技术方案", S["h3"]))
    story.append(Paragraph(
        "本发明采用如下技术方案：",
        S["body"]
    ))
    story.append(Paragraph(
        "一种半导体引线框的多层梯度镀覆方法，包括以下步骤：",
        S["body"]
    ))

    steps = [
        "步骤一：准备由铜合金形成的引线框基底，对所述基底进行表面清洁和活化处理；",
        "步骤二：采用电镀方式在所述基底表面形成厚度为 0.5-2.0 微米的镍（Ni）阻挡层，"
        "所述阻挡层用于阻止基底铜原子向外层扩散；",
        "步骤三：采用脉冲电镀方式在所述镍阻挡层上形成厚度为 1.0-3.0 微米的锡铟（Sn-In）"
        "合金过渡层，其中铟含量为 3-8 wt%，所述过渡层用于缓冲界面热应力；",
        "步骤四：采用脉冲电镀方式在所述过渡层上形成厚度为 5.0-10.0 微米的锡铟（Sn-In）"
        "合金表面层，其中铟含量为 3-8 wt%；",
        "步骤五：在超声波辅助搅拌条件下进行步骤三和步骤四的脉冲电镀，"
        "超声波频率为 20-40 kHz；",
        "步骤六：对镀覆完成的引线框进行后处理，包括清洗和干燥。",
    ]
    for s in steps:
        story.append(Paragraph(f"  {s}", S["claim"]))

    story.append(Paragraph(
        "其中，所述脉冲电镀的工艺参数为：峰值电流密度 40-60 ASD，占空比 30-50%，"
        "脉冲频率 50-200 Hz，由此获得的平均电流密度为 15-25 ASD。",
        S["body"]
    ))

    story.append(PageBreak())

    # ---- Beneficial Effects ----
    story.append(Paragraph("三、有益效果", S["h3"]))
    effects = [
        "（1）三层梯度结构通过 Ni 阻挡层阻止 Cu-Sn 互扩散形成脆性金属间化合物，"
        "从界面层面消除晶须生长的驱动力（压应力），比单一控制晶粒尺寸更为系统有效。",
        "（2）Sn-In 合金体系中铟的加入降低了镀层的内应力，同时提供优异的焊接浸润性；"
        "铟不在传统 Sn 合金添加元素（Ag/Bi/Cu/Zn）范围内，扩展了合金设计空间。",
        "（3）脉冲电镀工艺相比直流高电流密度电镀，镀层厚度均匀性更好，"
        "晶粒细化效果可通过脉冲参数灵活调控，且无需专用高速喷嘴设备。",
        "（4）超声波辅助搅拌可在低喷涂速度下实现均匀的离子补给，"
        "降低设备复杂度的同时提升镀层质量。",
        "（5）铜合金基底相比 Fe-Ni 合金具有更高的导热性和导电性，"
        "有利于高功率半导体封装的散热需求。",
    ]
    for e in effects:
        story.append(Paragraph(e, S["body_indent"]))

    # ---- Claims ----
    story.append(Paragraph("【权利要求书】", S["h2"]))

    claims = [
        ("1.", "一种半导体引线框的多层梯度镀覆方法，其特征在于，包括以下步骤：\n"
         "（a）准备由铜合金形成的引线框基底；\n"
         "（b）在所述基底表面形成厚度为 0.5-2.0 微米的镍阻挡层；\n"
         "（c）采用脉冲电镀方式在所述镍阻挡层上形成厚度为 1.0-3.0 微米的锡铟合金过渡层；\n"
         "（d）采用脉冲电镀方式在所述过渡层上形成厚度为 5.0-10.0 微米的锡铟合金表面层；\n"
         "其中，所述锡铟合金中铟的含量为 3-8 wt%。"),

        ("2.", "根据权利要求 1 所述的方法，其特征在于，所述脉冲电镀的工艺参数为："
         "峰值电流密度 40-60 ASD，占空比 30-50%，脉冲频率 50-200 Hz。"),

        ("3.", "根据权利要求 2 所述的方法，其特征在于，所述脉冲电镀过程中采用超声波辅助搅拌，"
         "超声波频率为 20-40 kHz。"),

        ("4.", "根据权利要求 1 所述的方法，其特征在于，所述锡铟合金还包含选自锑（Sb）"
         "和锗（Ge）中的至少一种元素，含量为 0.1-2.0 wt%。"),

        ("5.", "根据权利要求 1 所述的方法，其特征在于，所述铜合金为 C194 铜合金或 C7025 铜合金。"),

        ("6.", "根据权利要求 1 所述的方法，其特征在于，在步骤（b）之前还包括对基底进行酸洗活化处理。"),

        ("7.", "根据权利要求 1 所述的方法，其特征在于，在步骤（d）之后还包括选择性去除非功能区域镀层的步骤。"),

        ("8.", "一种半导体引线框，其特征在于，包括：\n"
         "铜合金基底；\n"
         "形成在所述基底表面的厚度为 0.5-2.0 微米的镍阻挡层；\n"
         "形成在所述镍阻挡层上的厚度为 1.0-3.0 微米的锡铟合金过渡层；以及\n"
         "形成在所述过渡层上的厚度为 5.0-10.0 微米的锡铟合金表面层；\n"
         "其中，所述锡铟合金中铟的含量为 3-8 wt%。"),

        ("9.", "根据权利要求 8 所述的半导体引线框，其特征在于，所述镍阻挡层、过渡层和表面层"
         "构成的多层梯度结构的总厚度为 6.5-15.0 微米。"),

        ("10.", "根据权利要求 8 所述的半导体引线框，其特征在于，所述锡铟合金表面层的"
         "晶须生长长度在 1000 小时 85°C/85%RH 加速试验后不超过 10 微米。"),

        ("11.", "一种半导体封装体，其特征在于，包括：\n"
         "权利要求 8-10 中任一项所述的半导体引线框；\n"
         "贴装在所述引线框的芯片贴装区上的半导体芯片；\n"
         "电连接所述半导体芯片与引线的键合线；以及\n"
         "包封所述芯片和键合线的模塑树脂。"),

        ("12.", "根据权利要求 11 所述的半导体封装体，其特征在于，所述引线的外部暴露表面上的"
         "多层梯度镀层在 260°C 回流焊条件下的焊料浸润角小于 30°。"),
    ]

    for num, text in claims:
        story.append(Paragraph(f"<b>{num}</b> {text}", S["claim"]))

    story.append(PageBreak())

    # ---- Abstract ----
    story.append(Paragraph("【摘要】", S["h2"]))
    story.append(Paragraph(
        "本发明公开了一种半导体引线框的多层梯度镀覆方法及引线框结构。该方法在铜合金基底上依次形成"
        "镍阻挡层（0.5-2.0μm）、锡铟合金过渡层（1.0-3.0μm）和锡铟合金表面层（5.0-10.0μm），"
        "其中铟含量为 3-8 wt%。镀覆过程采用脉冲电镀（峰值 40-60 ASD，占空比 30-50%）配合"
        "超声波辅助搅拌（20-40 kHz）。三层梯度结构通过镍阻挡层阻止铜锡互扩散，通过锡铟合金降低"
        "内应力，从界面应力管理的角度系统抑制晶须生长，同时提供优异的焊接浸润性。"
        "本发明适用于高可靠性半导体封装的引线框表面处理。",
        S["body"]
    ))

    # ---- Key terms ----
    story.append(Paragraph("【主权项】", S["h3"]))
    story.append(Paragraph(
        "权利要求 1（方法）和权利要求 8（产品）为独立权利要求。",
        S["body"]
    ))

    story.append(Spacer(1, 8*mm))

    # =========================================================
    # PART C: MODIFICATION EXPLANATION
    # =========================================================
    story.append(Paragraph("第三部分：修改主张内容说明", S["h1"]))
    story.append(divider())

    story.append(Paragraph(
        "以下说明本申请相对于 CN1770440A 原专利各核心主张所做的具体修改及其技术理由：",
        S["body"]
    ))

    mod_data = [
        [hcell("序号"), hcell("修改项目"), hcell("原专利主张"), hcell("本申请修改后"), hcell("修改理由")],

        [cell("1", True), cell("基底材料"),
         cell("Fe-Ni 合金\n（42 号合金）"),
         cell("铜合金\n（C194 / C7025）"),
         cell("铜合金导热性是 Fe-Ni 的 10 倍以上，更适合高功率封装；"
              "同时从根本上脱离原权利要求 1 的基底材料限定")],

        [cell("2", True), cell("镀层结构"),
         cell("单层 Sn/Sn合金\n晶粒 <1μm"),
         cell("三层梯度结构：\nNi 阻挡层 +\nSn-In 过渡层 +\nSn-In 表面层"),
         cell("多层梯度结构从「界面应力管理」角度抑制晶须，"
              "比单纯「晶粒尺寸控制」更系统；"
              "结构差异使其不落入「晶粒<1μm的镀层」的限定")],

        [cell("3", True), cell("合金体系"),
         cell("Sn-(Ag/Bi/Cu/Zn)\n添加量 <5%"),
         cell("Sn-In\n（In: 3-8 wt%）\n可选 Sb/Ge"),
         cell("In（铟）不在原专利列举的四种元素范围内；"
              "In 含量 3-8% 跨越原专利 5% 的上限；"
              "In 可降低 Sn 内应力并改善浸润性")],

        [cell("4", True), cell("电镀方式"),
         cell("直流电镀\n电流密度 ≥30 ASD"),
         cell("脉冲电镀\n峰值 40-60 ASD\n平均 15-25 ASD"),
         cell("脉冲电镀平均电流密度低于 30 ASD，不落入原权利要求 14 的限定；"
              "脉冲方式可通过占空比灵活控制晶粒结构")],

        [cell("5", True), cell("搅拌方式"),
         cell("高速喷嘴喷涂\n速度 >1 m/s"),
         cell("超声波辅助搅拌\n频率 20-40 kHz"),
         cell("超声波搅拌属于不同的物理机制（声空化 vs 机械射流）；"
              "不涉及喷嘴和喷涂速度，完全脱离原权利要求 15-16")],

        [cell("6", True), cell("底层处理"),
         cell("Sn 刮平层\n~0.2μm\n+ Ag 外层"),
         cell("Ni 阻挡层\n0.5-2.0μm\n（兼防扩散功能）"),
         cell("Ni 阻挡层材料、厚度、功能均与原 Sn 刮平层不同；"
              "取消 Ag 层，以 Ni 层兼顾阻挡和底层功能")],
    ]
    t = Table(mod_data, colWidths=[12*mm, 22*mm, 30*mm, 32*mm, 55*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), HDR_BG),
        ("GRID",(0,0),(-1,-1), 0.5, BORDER),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("BACKGROUND",(0,1),(0,-1), LIGHT_BG),
        ("BACKGROUND",(1,2),(-1,2), ROW_ALT),
        ("BACKGROUND",(1,4),(-1,4), ROW_ALT),
        ("BACKGROUND",(1,6),(-1,6), ROW_ALT),
    ]))
    story.append(t)

    story.append(Spacer(1, 8*mm))

    # ---- Final notes ----
    story.append(Paragraph("附注", S["h2"]))

    story.append(colored_box(
        "1. 专利状态提醒：CN1770440A 已于 2025-09-29 届满过期，任何人均可自由实施其技术方案。"
        "本申请的规避设计同时构成独立的技术创新（多层梯度结构 + Sn-In 合金 + 脉冲电镀），"
        "可作为新的发明专利申请予以保护。\n\n"
        "2. 建议事项：正式提交前，建议委托专利代理机构进行：\n"
        "   (a) 全面新颖性与创造性检索（特别是 Sn-In 合金电镀和多层镀层领域）；\n"
        "   (b) 权利要求的进一步优化和分层设计；\n"
        "   (c) 补充具体实施例数据（如晶须测试、浸润角测试、热循环测试结果）。\n\n"
        "3. 本文件为草案，仅供技术参考，不构成法律意见。",
        YELLOW_BG, HexColor("#d69e2e"), "body"
    ))

    story.append(Spacer(1, 5*mm))
    story.append(divider())
    story.append(Paragraph(
        "本报告由 AI 辅助生成，仅供技术研发与专利布局参考。如需正式申请，请咨询专利代理人。",
        S["small"]
    ))

    doc.build(story)
    print(f"Patent application draft saved to: {doc.filename}")


if __name__ == "__main__":
    build()
