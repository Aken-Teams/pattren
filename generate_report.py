#!/usr/bin/env python3
"""Generate Simplified Chinese patent comparison PDF report."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Font Registration ---
# Try to register a Chinese font
FONT_NAME = "SimSun"
FONT_BOLD = "SimSun"
font_registered = False

font_paths = [
    ("SimSun", r"C:\Windows\Fonts\simsun.ttc"),
    ("SimSun", r"C:\Windows\Fonts\simsun.ttf"),
    ("Microsoft YaHei", r"C:\Windows\Fonts\msyh.ttc"),
    ("Microsoft YaHei", r"C:\Windows\Fonts\msyh.ttf"),
    ("SimHei", r"C:\Windows\Fonts\simhei.ttf"),
]

for name, path in font_paths:
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            FONT_NAME = name
            FONT_BOLD = name
            font_registered = True
            print(f"Using font: {name} from {path}")
            break
        except Exception as e:
            print(f"Failed to register {name}: {e}")

if not font_registered:
    print("WARNING: No Chinese font found, falling back to Helvetica")
    FONT_NAME = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"

# --- Colors ---
PRIMARY = HexColor("#1a365d")
SECONDARY = HexColor("#2b6cb0")
ACCENT = HexColor("#3182ce")
LIGHT_BG = HexColor("#ebf8ff")
BORDER = HexColor("#bee3f8")
HEADER_BG = HexColor("#1a365d")
ROW_ALT = HexColor("#f7fafc")
GREEN = HexColor("#276749")
ORANGE = HexColor("#c05621")
RED = HexColor("#c53030")
LIGHT_GREEN = HexColor("#f0fff4")
LIGHT_ORANGE = HexColor("#fffaf0")
LIGHT_RED = HexColor("#fff5f5")

# --- Styles ---
styles = {
    "cover_title": ParagraphStyle(
        "cover_title", fontName=FONT_NAME, fontSize=28,
        textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=8*mm,
        leading=36
    ),
    "cover_subtitle": ParagraphStyle(
        "cover_subtitle", fontName=FONT_NAME, fontSize=14,
        textColor=SECONDARY, alignment=TA_CENTER, spaceAfter=4*mm,
        leading=20
    ),
    "cover_info": ParagraphStyle(
        "cover_info", fontName=FONT_NAME, fontSize=11,
        textColor=HexColor("#4a5568"), alignment=TA_CENTER,
        spaceAfter=3*mm, leading=16
    ),
    "h1": ParagraphStyle(
        "h1", fontName=FONT_NAME, fontSize=18, textColor=PRIMARY,
        spaceBefore=10*mm, spaceAfter=6*mm, leading=24
    ),
    "h2": ParagraphStyle(
        "h2", fontName=FONT_NAME, fontSize=14, textColor=SECONDARY,
        spaceBefore=6*mm, spaceAfter=4*mm, leading=20
    ),
    "h3": ParagraphStyle(
        "h3", fontName=FONT_NAME, fontSize=12, textColor=ACCENT,
        spaceBefore=4*mm, spaceAfter=3*mm, leading=16
    ),
    "body": ParagraphStyle(
        "body", fontName=FONT_NAME, fontSize=10, textColor=black,
        alignment=TA_JUSTIFY, spaceAfter=3*mm, leading=16
    ),
    "body_small": ParagraphStyle(
        "body_small", fontName=FONT_NAME, fontSize=9, textColor=black,
        alignment=TA_LEFT, leading=14
    ),
    "table_header": ParagraphStyle(
        "table_header", fontName=FONT_NAME, fontSize=9,
        textColor=white, alignment=TA_CENTER, leading=13
    ),
    "table_cell": ParagraphStyle(
        "table_cell", fontName=FONT_NAME, fontSize=8.5,
        textColor=HexColor("#2d3748"), alignment=TA_LEFT, leading=13
    ),
    "table_cell_center": ParagraphStyle(
        "table_cell_center", fontName=FONT_NAME, fontSize=8.5,
        textColor=HexColor("#2d3748"), alignment=TA_CENTER, leading=13
    ),
    "bullet": ParagraphStyle(
        "bullet", fontName=FONT_NAME, fontSize=10, textColor=black,
        leftIndent=15, spaceAfter=2*mm, leading=15,
        bulletIndent=5, bulletFontSize=10
    ),
    "conclusion": ParagraphStyle(
        "conclusion", fontName=FONT_NAME, fontSize=10,
        textColor=HexColor("#2d3748"), alignment=TA_JUSTIFY,
        spaceAfter=3*mm, leading=16, backColor=LIGHT_BG,
        borderPadding=(8, 8, 8, 8)
    ),
}


def make_header_cell(text):
    return Paragraph(text, styles["table_header"])

def make_cell(text, center=False):
    st = styles["table_cell_center"] if center else styles["table_cell"]
    return Paragraph(text, st)

def divider():
    """Create a styled divider line."""
    t = Table([[""]],  colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build_report(output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )
    story = []
    page_w = A4[0] - 40*mm  # usable width

    # ===== COVER PAGE =====
    story.append(Spacer(1, 40*mm))

    # Title block with border
    cover_data = [[
        Paragraph("专利技术比对分析报告", styles["cover_title"])
    ], [
        Paragraph("侧面浸润 / 引脚 / 切割 — 半导体封装领域", styles["cover_subtitle"])
    ]]
    cover_table = Table(cover_data, colWidths=[page_w])
    cover_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, -1), (-1, -1), 2, PRIMARY),
        ("LINEABOVE", (0, 0), (-1, 0), 2, PRIMARY),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 15*mm))

    # Cover info
    info_lines = [
        "比对专利数量：3 件",
        "技术领域：半导体封装 — 引线框架 / 引脚侧面处理 / 切割工艺",
        "报告日期：2026 年 3 月 23 日",
        "关键词：侧面浸润（Side Wetting）、引脚切割（Lead Cutting）、电镀（Plating）",
    ]
    for line in info_lines:
        story.append(Paragraph(line, styles["cover_info"]))

    story.append(Spacer(1, 20*mm))

    # Patent list on cover
    patent_summary = [
        [make_header_cell("序号"), make_header_cell("专利号"), make_header_cell("名称"), make_header_cell("申请人")],
        [make_cell("1", True), make_cell("CN1770440A"), make_cell("半导体引线框及电镀方法"), make_cell("Samsung Techwin")],
        [make_cell("2", True), make_cell("CN103094237A"), make_cell("半导体封装"), make_cell("Samsung Electro Mechanics")],
        [make_cell("3", True), make_cell("US9349679B2"), make_cell("半导体封装分离方法\n（引脚侧面电镀）"), make_cell("UTAC Thai Ltd")],
    ]
    t = Table(patent_summary, colWidths=[15*mm, 35*mm, 60*mm, 55*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("BACKGROUND", (0, 1), (-1, 1), ROW_ALT),
        ("BACKGROUND", (0, 3), (-1, 3), ROW_ALT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ===== 1. PATENT OVERVIEW =====
    story.append(Paragraph("一、专利基本信息概览", styles["h1"]))
    story.append(divider())

    # --- Patent 1 ---
    story.append(Paragraph("1.1  CN1770440A — 半导体引线框及电镀方法", styles["h2"]))
    p1_data = [
        [make_header_cell("项目"), make_header_cell("内容")],
        [make_cell("专利号"), make_cell("CN1770440A")],
        [make_cell("名称"), make_cell("半导体引线框及电镀方法，有半导体引线框的半导体封装")],
        [make_cell("申请人"), make_cell("Samsung Techwin Co Ltd（现 Hanwha Vision Co Ltd）")],
        [make_cell("发明人"), make_cell("崔祐硕、金重道、金银熙、李秀奉")],
        [make_cell("申请日"), make_cell("2005-09-29")],
        [make_cell("授权日"), make_cell("2010-05-05")],
        [make_cell("状态"), make_cell("已过期（2025-09-29届满）")],
        [make_cell("权利要求数"), make_cell("19 项")],
    ]
    t = Table(p1_data, colWidths=[35*mm, page_w - 35*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("BACKGROUND", (0, 1), (0, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("技术摘要：", styles["h3"]))
    story.append(Paragraph(
        "本发明通过在 Fe-Ni 合金（42 号合金）基底上镀覆晶粒尺寸小于 1 微米的锡或锡合金镀层，"
        "有效抑制晶须（Whisker）生长。采用高电流密度（≥30 ASD）配合高速喷嘴搅动（>1 m/s）的电镀工艺，"
        "在提高生产效率的同时将晶须最大长度控制在 20 微米以内，防止引线框失效。",
        styles["body"]
    ))

    # --- Patent 2 ---
    story.append(Paragraph("1.2  CN103094237A — 半导体封装", styles["h2"]))
    p2_data = [
        [make_header_cell("项目"), make_header_cell("内容")],
        [make_cell("专利号"), make_cell("CN103094237A")],
        [make_cell("名称"), make_cell("半导体封装")],
        [make_cell("申请人"), make_cell("Samsung Electro Mechanics Co Ltd")],
        [make_cell("发明人"), make_cell("林昶贤、许畅宰、李荣基、朴成根")],
        [make_cell("申请日"), make_cell("2011-12-30")],
        [make_cell("权利要求数"), make_cell("18 项（两组独立权利要求体系）")],
    ]
    t = Table(p2_data, colWidths=[35*mm, page_w - 35*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("BACKGROUND", (0, 1), (0, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("技术摘要：", styles["h3"]))
    story.append(Paragraph(
        "本发明公开了一种功率半导体封装结构，在衬底的第一表面和第二表面两侧分别形成第一和第二引线框架，"
        "两组引线框架以隔离距离基数交替排列。该设计在满足爬电距离和间隙距离等安全隔离条件的前提下，"
        "有效缩小模块整体尺寸，并扩大引线框架的布局空间。可选配散热板以提升散热性能。",
        styles["body"]
    ))

    # --- Patent 3 ---
    story.append(Paragraph("1.3  US9349679B2 — 半导体封装分离方法（侧面电镀）", styles["h2"]))
    p3_data = [
        [make_header_cell("项目"), make_header_cell("内容")],
        [make_cell("专利号"), make_cell("US9349679B2")],
        [make_cell("名称"), make_cell("Singulation method for semiconductor package with plating on side of connectors")],
        [make_cell("申请人"), make_cell("UTAC Thai Ltd（现 UTAC Headquarters Pte Ltd）")],
        [make_cell("发明人"), make_cell("Saravuth Sirinorakul, Somchai Nondhasitthichai")],
        [make_cell("申请日"), make_cell("2011-08-19")],
        [make_cell("授权日"), make_cell("2016-05-24")],
        [make_cell("有效期至"), make_cell("2033-06-11")],
    ]
    t = Table(p3_data, colWidths=[35*mm, page_w - 35*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("BACKGROUND", (0, 1), (0, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("技术摘要：", styles["h3"]))
    story.append(Paragraph(
        "本发明涉及半导体封装的分离（Singulation）方法。核心流程为：将多颗芯片贴装在共用引线框架上并用模塑料包封后，"
        "通过刀片切割引线框架进行分离，使引脚侧面暴露；随后对暴露的侧面进行金属电镀（锡/银/金/镍钯金等），"
        "以防止铜基底氧化，显著提升侧面浸润性（Side Wetting）和焊接可靠性。"
        "支持全切、半切及斜切等多种切割模式。",
        styles["body"]
    ))

    story.append(PageBreak())

    # ===== 2. TECHNICAL COMPARISON =====
    story.append(Paragraph("二、核心技术特征比对", styles["h1"]))
    story.append(divider())

    # Main comparison table
    comp_headers = [
        make_header_cell("比对维度"),
        make_header_cell("CN1770440A\n引线框电镀"),
        make_header_cell("CN103094237A\n封装结构"),
        make_header_cell("US9349679B2\n侧面电镀"),
    ]
    col_w = [28*mm, 47*mm, 47*mm, 47*mm]

    comp_data = [comp_headers]

    rows = [
        ("技术领域",
         "引线框表面电镀工艺",
         "功率半导体封装结构设计",
         "封装分离与侧面电镀工艺"),
        ("核心技术\n问题",
         "Fe-Ni 合金基底上锡镀层产生晶须，导致短路或断路失效",
         "隔离距离要求限制了功率模块小型化",
         "切割后引脚侧面裸露铜易氧化，影响焊接浸润性"),
        ("解决方案",
         "通过高电流密度电镀使晶粒尺寸 <1μm，从根本上抑制晶须生长",
         "在衬底上下两面交替排列引线框架，在满足爬电距离的同时缩小尺寸",
         "切割分离后对引脚侧面进行金属电镀（Sn/Ag/Au），实现侧面浸润"),
        ("涉及的\n引脚处理",
         "引脚表面镀层质量控制（抑制晶须）",
         "引脚空间布局与隔离距离设计",
         "引脚切割后侧面电镀（Side Wetting）"),
        ("切割工艺",
         "未涉及切割工艺",
         "未涉及切割工艺",
         "核心技术：全切 / 半切 / 斜切刀片切割"),
        ("电镀材料",
         "Sn 或 Sn 合金（含 Ag/Bi/Cu/Zn <5%）",
         "不涉及电镀",
         "Sn、Ag、Au、Ni-Au、Ni-Pd、Ni-Pd-Au"),
        ("电镀参数",
         "电流密度 ≥30 ASD\n喷涂速度 >1 m/s\n镀层厚度 ~10μm\n晶粒尺寸 <1μm",
         "不适用",
         "未限定具体参数\n重点在侧面覆盖完整性"),
        ("关键结构",
         "Fe-Ni 合金基底 + 细晶粒镀层",
         "双面引线框架 + 散热板 + 衬底",
         "模塑封装体 + 侧面电镀引脚"),
    ]

    for label, c1, c2, c3 in rows:
        comp_data.append([
            make_cell(label),
            make_cell(c1),
            make_cell(c2),
            make_cell(c3),
        ])

    t = Table(comp_data, colWidths=col_w)
    base_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("BACKGROUND", (0, 1), (0, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    # Alternate row shading
    for i in range(1, len(comp_data)):
        if i % 2 == 0:
            base_style.append(("BACKGROUND", (1, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(base_style))
    story.append(t)

    story.append(PageBreak())

    # ===== 3. CLAIM COMPARISON =====
    story.append(Paragraph("三、权利要求范围比对", styles["h1"]))
    story.append(divider())

    claim_data = [
        [make_header_cell("维度"),
         make_header_cell("CN1770440A"),
         make_header_cell("CN103094237A"),
         make_header_cell("US9349679B2")],
        [make_cell("独立权利\n要求类型"),
         make_cell("产品（引线框）+ 方法（电镀方法）"),
         make_cell("产品（封装结构）×2 组"),
         make_cell("方法（分离方法）+ 产品（封装体）")],
        [make_cell("权利要求\n总数"),
         make_cell("19 项", True),
         make_cell("18 项", True),
         make_cell("20 项", True)],
        [make_cell("保护重点"),
         make_cell("镀层晶粒尺寸 <1μm\n高电流密度工艺参数\n合金组分限定"),
         make_cell("双面引线框架交替排列\n隔离距离基数\n散热板集成"),
         make_cell("切割后侧面电镀\n全切/半切切割模式\n斜面切割刀片")],
        [make_cell("材料限定"),
         make_cell("Fe-Ni 合金基底\nSn/Sn合金镀层\n添加金属 <5%"),
         make_cell("衬底材料灵活\n（陶瓷/阳极氧化金属/PCB）"),
         make_cell("铜引脚\n多种电镀金属可选")],
        [make_cell("工艺限定"),
         make_cell("电流密度 ≥30 ASD\n刮平电镀法\n喷嘴速度 >1 m/s"),
         make_cell("无具体工艺参数限定"),
         make_cell("切割深度/刀片厚度\n电镀时序灵活")],
    ]
    t = Table(claim_data, colWidths=[28*mm, 47*mm, 47*mm, 47*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("BACKGROUND", (0, 1), (0, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (1, 2), (-1, 2), ROW_ALT),
        ("BACKGROUND", (1, 4), (-1, 4), ROW_ALT),
        ("BACKGROUND", (1, 6), (-1, 6), ROW_ALT),
    ]))
    story.append(t)

    story.append(Spacer(1, 8*mm))

    # ===== 4. OVERLAP ANALYSIS =====
    story.append(Paragraph("四、技术重叠与差异分析", styles["h1"]))
    story.append(divider())

    story.append(Paragraph("4.1  技术交集（共同点）", styles["h2"]))
    commons = [
        "三件专利均属于半导体封装技术领域，涉及引线框架（Lead Frame）的制造或应用。",
        "CN1770440A 与 US9349679B2 均涉及引脚表面电镀处理，但目的和对象不同。",
        "三件专利均关注封装可靠性的提升 — 分别从晶须抑制、结构优化、氧化防护三个角度切入。",
    ]
    for c in commons:
        story.append(Paragraph(f"  {c}", styles["bullet"]))

    story.append(Paragraph("4.2  核心差异", styles["h2"]))

    diff_data = [
        [make_header_cell("差异点"), make_header_cell("分析")],
        [make_cell("技术聚焦"),
         make_cell("CN1770440A 聚焦镀层微观结构（晶粒尺寸）；CN103094237A 聚焦宏观封装结构布局；"
                    "US9349679B2 聚焦切割后侧面处理工艺")],
        [make_cell("与「侧面浸润」\n的关联度"),
         make_cell("CN1770440A —【低】仅涉及引脚表面镀层质量，未涉及侧面\n"
                    "CN103094237A —【低】纯结构设计，未涉及浸润性\n"
                    "US9349679B2 —【高】核心发明即为实现引脚侧面浸润")],
        [make_cell("与「切割」\n的关联度"),
         make_cell("CN1770440A —【无】不涉及切割\n"
                    "CN103094237A —【无】不涉及切割\n"
                    "US9349679B2 —【高】切割（Singulation）是核心步骤")],
        [make_cell("商业价值"),
         make_cell("CN1770440A — 已过期，可自由实施\n"
                    "CN103094237A — 需确认当前法律状态\n"
                    "US9349679B2 — 有效至 2033 年，需关注侵权风险")],
    ]
    t = Table(diff_data, colWidths=[30*mm, page_w - 30*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("BACKGROUND", (0, 1), (0, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (1, 2), (-1, 2), ROW_ALT),
        ("BACKGROUND", (1, 4), (-1, 4), ROW_ALT),
    ]))
    story.append(t)

    story.append(PageBreak())

    # ===== 5. RELEVANCE SCORING =====
    story.append(Paragraph("五、关键词关联度评分", styles["h1"]))
    story.append(divider())

    story.append(Paragraph(
        "以搜索关键词「侧面浸润」「引脚」「切割」为基准，对三件专利的技术关联度进行评分（满分 5 分）：",
        styles["body"]
    ))

    score_data = [
        [make_header_cell("关键词"), make_header_cell("CN1770440A"), make_header_cell("CN103094237A"), make_header_cell("US9349679B2")],
        [make_cell("侧面浸润\n(Side Wetting)"),
         make_cell("1 / 5\n仅涉及表面镀层，\n未针对侧面", True),
         make_cell("0 / 5\n不涉及浸润性", True),
         make_cell("5 / 5\n核心发明目标", True)],
        [make_cell("引脚\n(Lead/Pin)"),
         make_cell("5 / 5\n引线框引脚为\n直接处理对象", True),
         make_cell("4 / 5\n引线框架为\n结构组成部分", True),
         make_cell("5 / 5\n引脚侧面为\n处理对象", True)],
        [make_cell("切割\n(Cutting)"),
         make_cell("0 / 5\n不涉及", True),
         make_cell("0 / 5\n不涉及", True),
         make_cell("5 / 5\n分离切割为\n核心步骤", True)],
        [make_cell("综合得分"),
         make_cell("2.0 / 5", True),
         make_cell("1.3 / 5", True),
         make_cell("5.0 / 5", True)],
    ]
    t = Table(score_data, colWidths=[28*mm, 47*mm, 47*mm, 47*mm])
    score_style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("BACKGROUND", (0, 1), (0, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        # Highlight scores
        ("BACKGROUND", (3, 1), (3, 3), LIGHT_GREEN),
        ("BACKGROUND", (2, 1), (2, 3), LIGHT_RED),
        # Total row
        ("BACKGROUND", (0, -1), (-1, -1), HexColor("#edf2f7")),
        ("BACKGROUND", (3, -1), (3, -1), GREEN),
        ("TEXTCOLOR", (3, -1), (3, -1), white),
    ]
    t.setStyle(TableStyle(score_style))
    story.append(t)

    story.append(Spacer(1, 10*mm))

    # ===== 6. CONCLUSION =====
    story.append(Paragraph("六、结论与建议", styles["h1"]))
    story.append(divider())

    story.append(Paragraph("6.1  总结", styles["h2"]))
    story.append(Paragraph(
        "在三件比对专利中，US9349679B2 与搜索关键词「侧面浸润、引脚、切割」的关联度最高，"
        "其核心发明直接解决了半导体封装引脚切割后侧面浸润性不足的问题。"
        "CN1770440A 虽然涉及引脚电镀，但聚焦于晶须抑制而非侧面浸润。"
        "CN103094237A 主要关注封装结构布局优化，与侧面浸润和切割的关联度最低。",
        styles["body"]
    ))

    story.append(Paragraph("6.2  实务建议", styles["h2"]))

    suggestions = [
        "若企业正在开发侧面浸润型封装产品，US9349679B2（有效至 2033 年）为主要规避对象，"
        "需仔细评估其权利要求范围，特别是切割后电镀的工艺步骤。",
        "CN1770440A 已于 2025 年 9 月过期，其高电流密度细晶粒电镀技术可自由实施，"
        "可考虑将其与侧面电镀工艺结合使用以提升镀层质量。",
        "建议进一步检索 US9349679B2 的中国同族专利或相关引用专利，"
        "以完整评估中国区的专利风险。",
        "可基于本比对结果，进一步扩展检索范围，加入关键词如「QFN」「DFN」「可焊性」"
        "「无引脚封装」等，以获取更全面的专利态势分析。",
    ]
    for i, s in enumerate(suggestions, 1):
        story.append(Paragraph(f"  {i}. {s}", styles["bullet"]))

    story.append(Spacer(1, 10*mm))

    # Footer disclaimer
    disclaimer = Paragraph(
        "声明：本报告基于公开专利数据库检索结果生成，仅供技术参考。"
        "如需用于法律决策，请咨询专业专利律师。",
        ParagraphStyle("disclaimer", fontName=FONT_NAME, fontSize=8,
                       textColor=HexColor("#a0aec0"), alignment=TA_CENTER, leading=12)
    )
    story.append(divider())
    story.append(disclaimer)

    # Build
    doc.build(story)
    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    output = r"D:\Code\pattren\patent_comparison_report.pdf"
    build_report(output)
