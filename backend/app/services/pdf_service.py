"""
Genera PDF por módulo con formato enriquecido: encabezados, negrita/cursiva,
bloques de código, listas y tablas — parseados desde markdown básico que la
IA produce naturalmente en el contenido del módulo.
"""
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, HRFlowable,
    Table, TableStyle, Preformatted
)
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor

OUTPUT_DIR = "generated_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _inline_markdown(text: str) -> str:
    """Convierte **negrita**, *cursiva* y `código` inline a tags que ReportLab entiende."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`', r'<font face="Courier">\1</font>', text)
    return text


def _parse_table(lines: list, start: int) -> tuple:
    """Parsea una tabla markdown (| col | col |) desde start. Devuelve (Table, siguiente_indice)."""
    rows = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        if not re.match(r'^\|[\s:|-]+\|$', lines[i].strip()):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows.append(cells)
        i += 1
    if not rows:
        return None, start + 1

    num_cols = len(rows[0])
    available_width = 6.0 * inch
    col_width = available_width / num_cols

    cell_style = ParagraphStyle('cell', fontName='Times-Roman', fontSize=9, leading=12, textColor=HexColor("#2D3748"))
    header_style = ParagraphStyle('cellh', fontName='Times-Bold', fontSize=9, leading=12, textColor=HexColor("#FFFFFF"))

    wrapped_rows = []
    for ri, row in enumerate(rows):
        style = header_style if ri == 0 else cell_style
        wrapped_rows.append([Paragraph(cell, style) for cell in row])

    table = Table(wrapped_rows, hAlign='LEFT', colWidths=[col_width] * num_cols)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#DD6B20")),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#CBD5E0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), HexColor("#F7FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return table, i


def _build_story_from_markdown(text: str, styles: dict) -> list:
    """Convierte markdown básico (##, ```, listas, tablas, negrita/cursiva/código) en flowables."""
    story = []
    lines = text.split("\n")
    i = 0
    in_code_block = False
    code_buffer = []

    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_buffer = []
            else:
                in_code_block = False
                story.append(Preformatted("\n".join(code_buffer), styles["code"]))
                story.append(Spacer(1, 0.1 * inch))
            i += 1
            continue

        if in_code_block:
            code_buffer.append(line)
            i += 1
            continue

        if line.strip().startswith("|"):
            table, next_i = _parse_table(lines, i)
            if table:
                story.append(table)
                story.append(Spacer(1, 0.15 * inch))
            i = next_i
            continue

        if line.strip().startswith("###"):
            story.append(Paragraph(_inline_markdown(line.strip("# ").strip()), styles["h3"]))
            i += 1
            continue
        if line.strip().startswith("##"):
            story.append(Paragraph(_inline_markdown(line.strip("# ").strip()), styles["h2"]))
            i += 1
            continue

        if re.match(r'^\s*[-*]\s+', line):
            bullet_text = re.sub(r'^\s*[-*]\s+', '', line)
            story.append(Paragraph("•  " + _inline_markdown(bullet_text), styles["bullet"]))
            i += 1
            continue

        if line.strip():
            story.append(Paragraph(_inline_markdown(line.strip()), styles["body"]))
            story.append(Spacer(1, 0.08 * inch))

        i += 1

    return story


def generate_module_pdf(module_title: str, content: str, description: str, filename: str) -> str:
    filepath = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(
        filepath, pagesize=letter,
        topMargin=0.75*inch, bottomMargin=0.75*inch, leftMargin=0.75*inch, rightMargin=0.75*inch
    )

    base = getSampleStyleSheet()
    primary_color = HexColor("#1A365D")
    secondary_color = HexColor("#4A5568")
    accent_color = HexColor("#DD6B20")

    styles = {
        "title": ParagraphStyle('T', parent=base['Heading1'], fontName='Helvetica-Bold', fontSize=24, leading=28, textColor=primary_color, spaceAfter=6),
        "desc": ParagraphStyle('D', parent=base['Italic'], fontName='Helvetica-Oblique', fontSize=11, leading=14, textColor=secondary_color, spaceAfter=15),
        "h2": ParagraphStyle('H2', parent=base['Heading2'], fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=accent_color, spaceBefore=14, spaceAfter=8),
        "h3": ParagraphStyle('H3', parent=base['Heading3'], fontName='Helvetica-Bold', fontSize=12.5, leading=16, textColor=primary_color, spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle('B', parent=base['BodyText'], fontName='Helvetica', fontSize=10.5, leading=16, textColor=HexColor("#2D3748"), alignment=4),
        "bullet": ParagraphStyle('BL', parent=base['BodyText'], fontName='Helvetica', fontSize=10.5, leading=15, textColor=HexColor("#2D3748"), leftIndent=14, spaceAfter=4),
        "code": ParagraphStyle('C', parent=base['Code'], fontName='Courier', fontSize=9, leading=12, backColor=HexColor("#F7FAFC"), borderColor=HexColor("#CBD5E0"), borderWidth=0.5, borderPadding=8, textColor=HexColor("#1A202C")),
    }

    story = [
        Paragraph(module_title, styles["title"]),
        Paragraph(description, styles["desc"]),
        HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=15),
    ]

    image_path = filepath.replace(".pdf", ".png")
    if os.path.exists(image_path):
        story.append(Image(image_path, width=5.5*inch, height=3.6*inch))
        story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Desarrollo de Contenido", styles["h2"]))
    story.extend(_build_story_from_markdown(content, styles))

    doc.build(story)
    return filepath