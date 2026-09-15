from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


INK = colors.HexColor("#171916")
MUTED = colors.HexColor("#696D66")
GREEN = colors.HexColor("#42634A")
PAPER = colors.HexColor("#F4F4F1")
LINE = colors.HexColor("#D9DBD5")
FONT = "ArialUnicode"


def inline(text: str) -> str:
    escaped = html.escape(text.strip())
    escaped = re.sub(r"`([^`]+)`", r"<font color='#315C3A'>\1</font>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    return escaped


def build_styles():
    pdfmetrics.registerFont(TTFont(FONT, "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"))
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontName=FONT, fontSize=27, leading=36, textColor=INK, alignment=TA_CENTER, spaceAfter=6 * mm),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=FONT, fontSize=18, leading=25, textColor=INK, spaceBefore=6 * mm, spaceAfter=3 * mm, keepWithNext=True),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=FONT, fontSize=14, leading=20, textColor=GREEN, spaceBefore=4 * mm, spaceAfter=2 * mm, keepWithNext=True),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName=FONT, fontSize=10.0, leading=16, textColor=INK, alignment=TA_LEFT, spaceAfter=2.1 * mm),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName=FONT, fontSize=8.5, leading=13, textColor=MUTED, spaceAfter=2 * mm),
        "bullet": ParagraphStyle("bullet", parent=base["BodyText"], fontName=FONT, fontSize=9.8, leading=15, textColor=INK),
        "table": ParagraphStyle("table", parent=base["BodyText"], fontName=FONT, fontSize=8.2, leading=11.5, textColor=INK),
    }


def page_decoration(canvas, document):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(PAPER)
    canvas.rect(0, height - 13 * mm, width, 13 * mm, fill=1, stroke=0)
    canvas.setFont(FONT, 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(17 * mm, height - 8.5 * mm, document.pickerroy_header)
    canvas.drawRightString(width - 17 * mm, 9 * mm, f"{document.page}")
    canvas.setStrokeColor(LINE)
    canvas.line(17 * mm, 13 * mm, width - 17 * mm, 13 * mm)
    canvas.restoreState()


def image_flow(path: Path, max_width: float, max_height: float):
    with PILImage.open(path) as im:
        width, height = im.size
    scale = min(max_width / width, max_height / height)
    return Image(str(path), width=width * scale, height=height * scale)


def parse_markdown(path: Path, styles: dict) -> list:
    lines = path.read_text(encoding="utf-8").splitlines()
    story: list = []
    index = 0
    first_heading = True
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        image_match = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", line)
        if image_match:
            image_path = (path.parent / image_match.group(2)).resolve()
            max_height = 92 * mm if "Logo" not in image_match.group(1) else 63 * mm
            visual = image_flow(image_path, 174 * mm, max_height)
            story.extend([Spacer(1, 2 * mm), visual, Spacer(1, 4 * mm)])
            index += 1
            continue
        if line.startswith("# "):
            if not first_heading:
                story.append(PageBreak())
            story.append(Paragraph(inline(line[2:]), styles["title"] if first_heading else styles["h1"]))
            first_heading = False
            index += 1
            continue
        if line.startswith("## "):
            story.append(Paragraph(inline(line[3:]), styles["h1"]))
            index += 1
            continue
        if line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), styles["h2"]))
            index += 1
            continue
        if line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                    rows.append([Paragraph(inline(cell), styles["table"]) for cell in cells])
                index += 1
            if rows:
                widths = [174 * mm / len(rows[0])] * len(rows[0])
                table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), GREEN),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), FONT),
                    ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.extend([table, Spacer(1, 3 * mm)])
            continue
        if line.startswith("- "):
            items = []
            while index < len(lines) and lines[index].strip().startswith("- "):
                items.append(ListItem(Paragraph(inline(lines[index].strip()[2:]), styles["bullet"]), leftIndent=4 * mm))
                index += 1
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=5 * mm, bulletFontName=FONT, bulletFontSize=7))
            story.append(Spacer(1, 2 * mm))
            continue
        if re.match(r"^\d+\. ", line):
            items = []
            while index < len(lines) and re.match(r"^\d+\. ", lines[index].strip()):
                body = re.sub(r"^\d+\. ", "", lines[index].strip())
                items.append(ListItem(Paragraph(inline(body), styles["bullet"]), leftIndent=5 * mm))
                index += 1
            story.append(ListFlowable(items, bulletType="1", start="1", leftIndent=7 * mm, bulletFontName=FONT, bulletFontSize=9))
            story.append(Spacer(1, 2 * mm))
            continue
        paragraph = [line]
        index += 1
        while index < len(lines):
            upcoming = lines[index].strip()
            if not upcoming or upcoming.startswith(("#", "|", "- ")) or re.match(r"^\d+\. ", upcoming) or upcoming.startswith("!["):
                break
            paragraph.append(upcoming)
            index += 1
        text = " ".join(paragraph)
        style = styles["small"] if text.startswith("版本 ") else styles["body"]
        story.append(Paragraph(inline(text), style))
    return story


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--title", default="PickerRoy 使用说明书")
    parser.add_argument("--subject", default="PickerRoy 0.3.2 安装、使用、个性化学习、导出与排错")
    parser.add_argument("--header", default="PickerRoy · 本地视频静帧筛选")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    styles = build_styles()
    document = SimpleDocTemplate(
        str(args.output),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=19 * mm,
        bottomMargin=17 * mm,
        title=args.title,
        author="PickerRoy",
        subject=args.subject,
    )
    document.pickerroy_header = args.header
    document.build(parse_markdown(args.markdown.resolve(), styles), onFirstPage=page_decoration, onLaterPages=page_decoration)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
