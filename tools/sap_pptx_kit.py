"""
Shared Snowflake-template PPTX toolkit.

Extracted verbatim from build_deck.py so the one-pager reuses exactly the
helpers and verifiers that produced the verified 15-slide deck, rather than a
second copy that could drift. build_deck.py is deliberately left untouched.
"""

#!/usr/bin/env python3
"""Supply Chain Demo Overview — Snowflake-branded deck (15 slides)."""

import os
import math
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.oxml.ns import qn
from lxml import etree

# ───────────────────────── Palette (core-branding.md §4) ─────────────────────────
DK1       = RGBColor(0x26, 0x26, 0x26)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
DK2       = RGBColor(0x11, 0x56, 0x7F)
SF_BLUE   = RGBColor(0x29, 0xB5, 0xE8)
TEAL      = RGBColor(0x71, 0xD3, 0xDC)
ORANGE    = RGBColor(0xFF, 0x9F, 0x36)
VIOLET    = RGBColor(0x7D, 0x44, 0xCF)
PINK      = RGBColor(0xD4, 0x5B, 0x90)
BODY_GREY = RGBColor(0x5B, 0x5B, 0x5B)
TBL_GREY  = RGBColor(0x71, 0x71, 0x71)
MUTED     = RGBColor(0xBF, 0xBF, 0xBF)
LIGHT_BG  = RGBColor(0xF5, 0xF5, 0xF5)
BORDER    = RGBColor(0xC8, 0xC8, 0xC8)

# Fill → Text contrast lookup (MANDATORY — TEAL/ORANGE never take WHITE)
FILL_TEXT = {
    "DK2": WHITE, "SF_BLUE": WHITE, "TEAL": DK1,
    "ORANGE": DK1, "VIOLET": WHITE, "PINK": WHITE,
}


# ───────────────────────── Helpers (core-helpers.md §9, §12.7) ─────────────────────────
def set_ph(slide, idx, text):
    ph = slide.placeholders[idx]
    t_pos = (ph.top or 0) / 914400
    if t_pos < 0.50:
        clean = text.replace('\n', ' ')
        if len(clean) > 50:
            print(f"⚠ TITLE TOO LONG: {len(clean)} chars (max 50): \"{clean[:50]}...\"")
    ph.text = text
    ph.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    bodyPr = ph.text_frame._txBody.find(f'{{{ns}}}bodyPr')
    if bodyPr is None:
        bodyPr = etree.SubElement(ph.text_frame._txBody, f'{{{ns}}}bodyPr')
    if t_pos < 0.50:
        bodyPr.set('bIns', '0')
    elif 0.60 < t_pos < 1.20:
        bodyPr.set('tIns', '54864')
    if t_pos < 1.20:
        for para in ph.text_frame.paragraphs:
            pPr = para._p.find(f'{{{ns}}}pPr')
            if pPr is None:
                pPr = etree.SubElement(para._p, f'{{{ns}}}pPr')
                para._p.insert(0, pPr)
            pPr.set('indent', '0')
            pPr.set('marL', '0')


def _pad_body_ph(ph):
    t_pos = (ph.top or 0) / 914400
    if t_pos > 1.20:
        ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        bodyPr = ph.text_frame._txBody.find(f'{{{ns}}}bodyPr')
        if bodyPr is None:
            bodyPr = etree.SubElement(ph.text_frame._txBody, f'{{{ns}}}bodyPr')
        bodyPr.set('bIns', '91440')
        ph.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE


def set_ph_lines(slide, idx, lines, font_size=None):
    ph = slide.placeholders[idx]
    tf = ph.text_frame
    tf.clear()
    _pad_body_ph(ph)
    lines = [l for l in lines if l.strip()]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        if font_size:
            p.font.size = Pt(font_size)


def set_ph_sections(slide, idx, sections, heading_size=None, body_size=None):
    ph = slide.placeholders[idx]
    tf = ph.text_frame
    tf.clear()
    _pad_body_ph(ph)
    ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    first = True
    for heading, body_lines in sections:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        p.level = 0
        if not first:
            pPr = p._p.find(f'{{{ns}}}pPr')
            if pPr is None:
                pPr = etree.SubElement(p._p, f'{{{ns}}}pPr')
                p._p.insert(0, pPr)
            spcBef = etree.SubElement(pPr, f'{{{ns}}}spcBef')
            spcPts = etree.SubElement(spcBef, f'{{{ns}}}spcPts')
            spcPts.set('val', '1400')
        first = False
        run = p.add_run()
        run.text = heading
        run.font.bold = True
        run.font.color.rgb = DK2
        if heading_size:
            run.font.size = Pt(heading_size)
        for line in body_lines:
            bp = tf.add_paragraph()
            bp.level = 1
            bp.text = line
            if body_size:
                bp.font.size = Pt(body_size)


def add_shape_text(slide, shape_type, left, top, width, height,
                   text, fill_colour, font_colour,
                   font_size=10, bold=False, alignment=PP_ALIGN.CENTER):
    """MANDATORY helper — every custom shape goes through here."""
    shape = slide.shapes.add_shape(
        shape_type, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_colour
    shape.line.fill.background()

    if width <= 2.0 and '\n' not in text and ' ' in text:
        text = text.replace(' ', '\n')

    tf = shape.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Pt(4)
    tf.margin_right = Pt(4)
    tf.margin_top = Pt(2)
    tf.margin_bottom = Pt(2)

    p = tf.paragraphs[0]
    p.text = text
    p.font.name = "Arial"
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = font_colour
    p.alignment = alignment
    return shape


def add_text(slide, left, top, width, height, text,
             font_size=9, colour=DK1, bold=False, alignment=PP_ALIGN.CENTER):
    """Plain textbox (labels / descriptions / footnotes). Arial enforced."""
    box = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = "Arial"
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = colour
    p.alignment = alignment
    return box


def set_table_borders(tbl, n_rows, n_cols):
    for ri in range(n_rows):
        for ci in range(n_cols):
            tc = tbl.cell(ri, ci)._tc
            tcPr = tc.find(qn("a:tcPr"))
            if tcPr is None:
                tcPr = etree.SubElement(tc, qn("a:tcPr"))
            for edge in ["lnL", "lnR", "lnT", "lnB"]:
                ln = etree.SubElement(tcPr, qn(f"a:{edge}"), w="12700")
                sf = etree.SubElement(ln, qn("a:solidFill"))
                etree.SubElement(sf, qn("a:srgbClr"), val="C8C8C8")


def style_cell(cell, text, fill, colour, size, bold=False,
               alignment=PP_ALIGN.LEFT):
    cell.text = str(text)
    cell.fill.solid()
    cell.fill.fore_color.rgb = fill
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.margin_left = Pt(6)
    cell.margin_right = Pt(6)
    cell.margin_top = Pt(2)
    cell.margin_bottom = Pt(2)
    for p in cell.text_frame.paragraphs:
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = colour
        p.font.name = "Arial"
        p.alignment = alignment


# ───────────────────────── verify_slide (verification.md §23) ─────────────────────────
def verify_slide(slide, prs, slide_num):
    issues = []
    safe_bottom = 5.10

    for shape in slide.placeholders:
        idx = shape.placeholder_format.idx
        if idx in (0, 1) and shape.has_text_frame:
            if not shape.text_frame.text.strip():
                label = "TITLE" if idx == 0 else "SUBTITLE"
                issues.append(f"  EMPTY {label}: PH[{idx}] has no text")

    for shape in slide.shapes:
        l = (shape.left or 0) / 914400
        t = (shape.top or 0) / 914400
        w = (shape.width or 0) / 914400
        h = (shape.height or 0) / 914400
        bot, right = t + h, l + w

        if not shape.is_placeholder and bot > safe_bottom and w > 0.5:
            issues.append(f"  OVERFLOW: shape at ({l:.2f}\",{t:.2f}\") bottom={bot:.2f}\" exceeds {safe_bottom}\"")
        if not shape.is_placeholder and t < 1.22 and w > 0.3 and h > 0.1:
            issues.append(f"  HEADER OVERLAP: shape at ({l:.2f}\",{t:.2f}\") starts above 1.22\"")
        if not shape.is_placeholder and w > 0.3:
            if right > 9.55:
                issues.append(f"  RIGHT OVERFLOW: shape at ({l:.2f}\",{t:.2f}\") right={right:.2f}\" > 9.50\"")
            if bot > 5.15:
                issues.append(f"  BOTTOM OVERFLOW: shape at ({l:.2f}\",{t:.2f}\") bottom={bot:.2f}\" > 5.10\"")

        if shape.has_table:
            n_rows = len(shape.table.rows)
            row_h = h / n_rows if n_rows else 0.40
            if bot > safe_bottom:
                issues.append(f"  TABLE OVERFLOW: {n_rows} rows, bottom={bot:.2f}\". Max {int((safe_bottom-t)/row_h)} rows.")

        if not shape.is_placeholder and shape.has_text_frame and not shape.has_table:
            tf = shape.text_frame
            total_chars = sum(len(p.text) for p in tf.paragraphs)
            if total_chars > 0 and w > 0.5 and h > 0.40:
                max_chars = int(w * 9) * max(int(h / 0.18), 1)
                if total_chars > max_chars * 1.2:
                    issues.append(f"  TEXT DENSE: shape ({w:.1f}\"x{h:.1f}\") has {total_chars} chars, max ~{max_chars}")

        if not shape.is_placeholder and shape.has_text_frame:
            st = shape.shape_type
            is_oval = (st and st == 9)
            is_small = w < 2.0 and h < 2.0
            if is_oval or is_small:
                max_fs = 0
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        if run.font.size and run.font.size.pt > max_fs:
                            max_fs = run.font.size.pt
                    if para.font.size and para.font.size.pt > max_fs:
                        max_fs = para.font.size.pt
                if is_oval:
                    d = min(w, h)
                    if d < 0.54:
                        issues.append(f"  CIRCLE TOO SMALL: {d:.2f}\" diameter (min 0.55\")")
                    if max_fs > 0:
                        if d <= 0.80 and max_fs > 14:
                            issues.append(f"  CIRCLE FONT TOO LARGE: {max_fs:.0f}pt in {d:.2f}\" circle (max 14pt)")
                        elif 0.80 < d <= 1.00 and max_fs > 10:
                            issues.append(f"  CIRCLE FONT TOO LARGE: {max_fs:.0f}pt in {d:.2f}\" circle (max 10pt)")
                        elif 1.00 < d <= 1.50 and max_fs > 11:
                            issues.append(f"  CIRCLE FONT TOO LARGE: {max_fs:.0f}pt in {d:.2f}\" circle (max 11pt)")
                if shape.shape_type and shape.shape_type != 17:
                    auto = shape.text_frame.auto_size
                    if (auto is None or auto == 0) and any(p.text.strip() for p in shape.text_frame.paragraphs):
                        issues.append(f"  NO AUTO-FIT: shape \"{shape.name}\" ({w:.2f}\"x{h:.2f}\") has text but no TEXT_TO_FIT_SHAPE")

    # Wall of text / dense placeholder / auto-fit on body PHs
    for shape in slide.shapes:
        if not shape.is_placeholder or not shape.has_text_frame:
            continue
        t = (shape.top or 0) / 914400
        if t <= 1.20:
            continue
        paras = shape.text_frame.paragraphs
        bold_heading_count = 0
        for pi, para in enumerate(paras):
            txt = para.text.strip()
            if not txt or len(txt) > 50:
                continue
            is_bold = any(r.font.bold for r in para.runs if r.font.bold is True) if para.runs else False
            if is_bold and pi + 1 < len(paras):
                nxt = paras[pi + 1].text.strip()
                if nxt and len(nxt) > len(txt):
                    bold_heading_count += 1
        if bold_heading_count >= 3:
            issues.append(f"  WALL OF TEXT: PH[{shape.placeholder_format.idx}] has {bold_heading_count} bold-header sections")

    has_visual = any(
        s.shape_type in (MSO_SHAPE_TYPE.AUTO_SHAPE, MSO_SHAPE_TYPE.FREEFORM, MSO_SHAPE_TYPE.TABLE)
        for s in slide.shapes if not s.is_placeholder)
    if not has_visual:
        for shape in slide.shapes:
            if not shape.is_placeholder or not shape.has_text_frame:
                continue
            if (shape.top or 0) / 914400 <= 1.20:
                continue
            non_empty = [p for p in shape.text_frame.paragraphs if p.text.strip()]
            if len(non_empty) >= 10:
                issues.append(f"  DENSE PLACEHOLDER: PH[{shape.placeholder_format.idx}] has {len(non_empty)} lines, no visuals")

    for shape in slide.shapes:
        if not shape.is_placeholder or not shape.has_text_frame:
            continue
        if (shape.top or 0) / 914400 <= 1.20:
            continue
        tf = shape.text_frame
        if sum(len(p.text) for p in tf.paragraphs) > 100:
            if tf.auto_size is None or tf.auto_size == 0:
                issues.append(f"  NO AUTO-FIT PH: PH[{shape.placeholder_format.idx}] Auto size is None")

    PALETTE = {
        (0x26,0x26,0x26), (0xFF,0xFF,0xFF), (0x11,0x56,0x7F), (0x29,0xB5,0xE8),
        (0x71,0xD3,0xDC), (0xFF,0x9F,0x36), (0x7D,0x44,0xCF), (0xD4,0x5B,0x90),
        (0x5B,0x5B,0x5B), (0x71,0x71,0x71), (0x92,0x92,0x92), (0xBF,0xBF,0xBF),
        (0xF5,0xF5,0xF5), (0xC8,0xC8,0xC8), (0xA2,0x00,0x00), (0xEF,0xEF,0xEF),
        (0xDD,0xDD,0xDD), (0xCC,0xCC,0xCC), (0x00,0x00,0x00),
    }
    SFBLUE_RGB = (0x29,0xB5,0xE8)
    ACCENT_FILL_ONLY = {(0x71,0xD3,0xDC), (0xFF,0x9F,0x36), (0x7D,0x44,0xCF), (0xD4,0x5B,0x90)}
    for shape in slide.shapes:
        if shape.is_placeholder or not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            sources = []
            for run in para.runs:
                try:
                    c = run.font.color
                    if c and c.type is not None:
                        sources.append((c.rgb, run.font.size, run.text))
                except AttributeError:
                    pass
            try:
                pc = para.font.color
                if pc and pc.type is not None:
                    sz = para.font.size or (para.runs[0].font.size if para.runs else None)
                    sources.append((pc.rgb, sz, para.text))
            except (AttributeError, IndexError):
                pass
            for rgb, sz, txt in sources:
                if rgb is None:
                    continue
                rt = (rgb[0], rgb[1], rgb[2])
                sz_pt = sz / 12700 if sz else 0
                in_pal = rt in PALETTE or any(all(abs(a-b) <= 10 for a, b in zip(rt, pcx)) for pcx in PALETTE)
                if not in_pal:
                    issues.append(f"  NON-PALETTE COLOR: #{rgb} on \"{txt[:20]}\"")
                if rt in ACCENT_FILL_ONLY:
                    issues.append(f"  ACCENT AS TEXT: #{rgb} on \"{txt[:20]}\" — fills only")
                if rt == SFBLUE_RGB and 0 < sz_pt < 28:
                    issues.append(f"  SF_BLUE UNDERSIZED: {sz_pt:.0f}pt on \"{txt[:20]}\" (min 28pt)")

    for shape in slide.shapes:
        if shape.is_placeholder:
            continue
        try:
            fill = shape.fill
            if fill and fill.type is not None and fill.type == 1:
                fc = fill.fore_color
                if fc and fc.type is not None and fc.rgb:
                    rt = (fc.rgb[0], fc.rgb[1], fc.rgb[2])
                    in_pal = rt in PALETTE or any(all(abs(a-b) <= 10 for a, b in zip(rt, pcx)) for pcx in PALETTE)
                    if not in_pal:
                        issues.append(f"  NON-PALETTE FILL: #{fc.rgb} on shape \"{shape.name}\"")
        except (AttributeError, TypeError):
            pass

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                if run.font.name and run.font.name != "Arial":
                    issues.append(f"  WRONG FONT: \"{run.font.name}\" on \"{run.text[:25]}\"")
            try:
                if para.font.name and para.font.name != "Arial":
                    issues.append(f"  WRONG FONT: \"{para.font.name}\" on \"{para.text[:25]}\"")
            except AttributeError:
                pass

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            if not para.text.strip():
                continue
            sizes = [r.font.size.pt for r in para.runs if r.font.size]
            if para.font.size:
                sizes.append(para.font.size.pt)
            for sz in sizes:
                if sz < 7:
                    issues.append(f"  FONT TOO SMALL: {sz:.0f}pt on \"{para.text[:25]}\"")
                elif sz > 32 and not shape.is_placeholder:
                    issues.append(f"  FONT TOO LARGE: {sz:.0f}pt on \"{para.text[:25]}\"")

    GENERIC = ["item 1", "item 2", "item 3", "lorem ipsum", "placeholder",
               "text here", "enter text", "your text", "todo", "tbd",
               "description here", "add content", "insert text", "sample text"]
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            txt = para.text.strip().lower()
            if not txt or len(txt) < 3:
                continue
            for gp in GENERIC:
                if gp in txt:
                    issues.append(f"  GENERIC TEXT: \"{para.text.strip()[:40]}\"")
                    break
            if not shape.is_placeholder:
                continue
            if (shape.top or 0) / 914400 > 1.20 and len(txt.split()) == 1 and len(txt) > 2:
                issues.append(f"  TERSE BULLET: \"{para.text.strip()}\" — single-word bullet")

    TEAL_RGB, ORANGE_RGB, WHITE_RGB = (0x71,0xD3,0xDC), (0xFF,0x9F,0x36), (0xFF,0xFF,0xFF)
    for shape in slide.shapes:
        if shape.is_placeholder or not shape.has_text_frame:
            continue
        try:
            fill = shape.fill
            if fill and fill.type is not None and fill.type == 1:
                fc = fill.fore_color
                if fc and fc.type is not None and fc.rgb:
                    ft = (fc.rgb[0], fc.rgb[1], fc.rgb[2])
                    for para in shape.text_frame.paragraphs:
                        cols = [r.font.color for r in para.runs]
                        try:
                            cols.append(para.font.color)
                        except AttributeError:
                            pass
                        for tc in cols:
                            try:
                                if tc and tc.type is not None and tc.rgb:
                                    tt = (tc.rgb[0], tc.rgb[1], tc.rgb[2])
                                    if ft == TEAL_RGB and tt == WHITE_RGB:
                                        issues.append(f"  BAD CONTRAST: TEAL fill + WHITE text on \"{para.text[:30]}\"")
                                    if ft == ORANGE_RGB and tt == WHITE_RGB:
                                        issues.append(f"  BAD CONTRAST: ORANGE fill + WHITE text on \"{para.text[:30]}\"")
                            except AttributeError:
                                pass
        except (AttributeError, TypeError):
            pass

    for shape in slide.shapes:
        if shape.is_placeholder or not shape.has_text_frame:
            continue
        try:
            if shape.line.fill.type is not None and shape.line.fill.type == 1:
                txt = shape.text_frame.text[:30] or shape.name
                issues.append(f"  VISIBLE OUTLINE: shape \"{txt}\" has a stroke")
        except (AttributeError, TypeError):
            pass

    for shape in slide.shapes:
        if shape.is_placeholder or not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            if len(para.runs) > 1:
                combined = "".join(r.text for r in para.runs)
                spaced = " ".join(r.text for r in para.runs)
                if combined != spaced and not any(c in combined for c in [' ', '\n']):
                    issues.append(f"  MERGED RUNS: \"{combined}\"")

    custom = [(s, (s.left or 0)/914400, (s.top or 0)/914400,
               (s.width or 0)/914400, (s.height or 0)/914400)
              for s in slide.shapes if not s.is_placeholder and (s.width or 0)/914400 > 0.5]
    reported = set()
    for i, (s1, l1, t1, w1, h1) in enumerate(custom):
        for j, (s2, l2, t2, w2, h2) in enumerate(custom):
            if j <= i or (i, j) in reported:
                continue
            r1, b1, r2, b2 = l1+w1, t1+h1, l2+w2, t2+h2
            if l1 < r2 and r1 > l2 and t1 < b2 and b1 > t2:
                ov_w = min(r1, r2) - max(l1, l2)
                ov_h = min(b1, b2) - max(t1, t2)
                same_col = abs((l1+w1/2) - (l2+w2/2)) < max(w1, w2) * 0.6
                if ov_w > 0.25 and ov_h > 0.25 and not same_col:
                    issues.append(f"  OVERLAP: shapes at ({l1:.1f}\",{t1:.1f}\") and ({l2:.1f}\",{t2:.1f}\") overlap {ov_w:.1f}\"x{ov_h:.1f}\"")
                    reported.add((i, j))

    for shape in slide.shapes:
        if not (shape.is_placeholder and shape.has_text_frame):
            continue
        tf = shape.text_frame
        idx = shape.placeholder_format.idx
        l = (shape.left or 0)/914400
        t = (shape.top or 0)/914400
        w = (shape.width or 0)/914400
        h = (shape.height or 0)/914400
        paras = tf.paragraphs
        if t < 0.50:
            tt = " ".join(p.text for p in paras)
            if len(tt) > 50:
                issues.append(f"  TITLE TOO LONG: {len(tt)} chars (max 50): \"{tt[:40]}...\"")
        if 0.60 < t < 1.20:
            st = " ".join(p.text for p in paras)
            if len(st) > 65:
                issues.append(f"  SUBTITLE TOO LONG: {len(st)} chars (max 65)")
        for pi, para in enumerate(paras):
            txt = para.text.strip()
            if not txt:
                continue
            if len(txt) < 40 and pi + 1 < len(paras):
                nxt = paras[pi+1].text.strip()
                if len(nxt) > 40 and para.level == paras[pi+1].level:
                    if not any(r.font.bold for r in para.runs if r.font.bold):
                        issues.append(f"  FLAT TEXT: PH heading \"{txt[:30]}\" not bold")
        if t > 1.20:
            empty_count = sum(1 for p in paras if not p.text.strip())
            if empty_count:
                issues.append(f"  EMPTY SPACERS: PH{idx} has {empty_count} empty paragraph(s)")
            content_paras = [p for p in paras if p.text.strip()]
            if len(content_paras) > 3 and set(p.level for p in content_paras) == {0}:
                issues.append(f"  FLAT HIERARCHY: PH{idx} has {len(content_paras)} paragraphs all at L0")
            total_chars = sum(len(p.text) for p in paras)
            if total_chars > 0 and w > 2.0:
                max_chars = int(w * 9) * int(h / 0.18)
                if total_chars > max_chars:
                    issues.append(f"  CONTENT DENSE: PH at ({l:.1f}\",{t:.1f}\") has {total_chars} chars, max ~{max_chars}")
        if l + w > 9.55:
            issues.append(f"  RIGHT OVERFLOW: PH at ({l:.2f}\",{t:.2f}\") right={l+w:.2f}\"")

    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            txt = para.text.strip()
            if len(txt) < 6:
                continue
            merged = re.findall(r'[a-z][A-Z]', txt)
            if len(merged) >= 1 and ' ' not in txt and '\n' not in txt and len(txt) > 8:
                issues.append(f"  MERGED TEXT: \"{txt[:40]}\"")
            if txt.isupper() and len(txt) > 12 and ' ' not in txt:
                if re.findall(r'[^AEIOU]{4,}', txt):
                    issues.append(f"  MERGED CAPS: \"{txt[:40]}\"")

    if issues:
        print(f"⚠ SLIDE {slide_num} issues:")
        for iss in issues:
            print(iss)
    else:
        print(f"✓ SLIDE {slide_num} OK")
    return issues


# ───────────────────────── verify_deck (verification.md) ─────────────────────────
def verify_deck(prs):
    issues = []
    content_slides = 0
    visual_pattern_slides = 0
    consecutive_text = 0
    max_consecutive_text = 0

    for si, slide in enumerate(prs.slides):
        is_cover = is_divider = is_thankyou = False
        has_custom_shapes = False
        for shape in slide.shapes:
            if shape.is_placeholder:
                t = (shape.top or 0) / 914400
                if t > 1.20 and hasattr(shape, 'placeholder_format'):
                    if shape.placeholder_format.idx == 3:
                        is_cover = True
            else:
                w = (shape.width or 0) / 914400
                h = (shape.height or 0) / 914400
                if w > 0.5 and h > 0.3:
                    has_custom_shapes = True
        try:
            ln = slide.slide_layout.name
            if "Quote" in ln and "Violet" in ln and "_1_1" in ln and not has_custom_shapes:
                is_divider = True
            if "Thank" in ln:
                is_thankyou = True
        except Exception:
            pass
        if not is_cover and not is_divider and not is_thankyou:
            content_slides += 1
            if has_custom_shapes:
                visual_pattern_slides += 1
                consecutive_text = 0
            else:
                consecutive_text += 1
                max_consecutive_text = max(max_consecutive_text, consecutive_text)

    if content_slides > 0:
        ratio = visual_pattern_slides / content_slides
        required = max(1, int(content_slides * 0.40))
        if visual_pattern_slides < required:
            issues.append(f"  LOW VISUAL DENSITY: {visual_pattern_slides}/{content_slides} ({ratio:.0%}) — need ≥{required}")
    if max_consecutive_text > 2:
        issues.append(f"  CONSECUTIVE TEXT: {max_consecutive_text} bullet-only slides in a row (max 2)")

    total = len(prs.slides)
    if total < 3:
        issues.append(f"  TOO SHORT: Only {total} slides")
    if total > 30:
        issues.append(f"  TOO LONG: {total} slides")

    non_arial = off_palette = generic = 0
    GENERIC = ["item 1", "item 2", "item 3", "lorem ipsum", "placeholder",
               "text here", "enter text", "your text", "todo", "tbd",
               "description here", "add content", "insert text", "sample text"]
    PALETTE = {
        (0x26,0x26,0x26), (0xFF,0xFF,0xFF), (0x11,0x56,0x7F), (0x29,0xB5,0xE8),
        (0x71,0xD3,0xDC), (0xFF,0x9F,0x36), (0x7D,0x44,0xCF), (0xD4,0x5B,0x90),
        (0x5B,0x5B,0x5B), (0x71,0x71,0x71), (0x92,0x92,0x92), (0xBF,0xBF,0xBF),
        (0xF5,0xF5,0xF5), (0xC8,0xC8,0xC8), (0xA2,0x00,0x00), (0xEF,0xEF,0xEF),
        (0xDD,0xDD,0xDD), (0xCC,0xCC,0xCC), (0x00,0x00,0x00),
    }
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                txt = para.text.strip().lower()
                if txt:
                    for gp in GENERIC:
                        if gp in txt:
                            generic += 1
                            break
                for run in para.runs:
                    if run.font.name and run.font.name != "Arial":
                        non_arial += 1
                    try:
                        c = run.font.color
                        if c and c.type is not None and c.rgb:
                            t = (c.rgb[0], c.rgb[1], c.rgb[2])
                            if not (t in PALETTE or any(all(abs(a-b) <= 10 for a, b in zip(t, pc)) for pc in PALETTE)):
                                off_palette += 1
                    except (AttributeError, TypeError):
                        pass
    if non_arial:
        issues.append(f"  BRAND: {non_arial} text run(s) using non-Arial font")
    if off_palette:
        issues.append(f"  BRAND: {off_palette} text run(s) using off-palette colours")
    if generic:
        issues.append(f"  CONTENT: {generic} instance(s) of generic placeholder text")

    weak = 0
    WEAK = ["we will", "we can", "things", "stuff", "various", "some of the"]
    for slide in prs.slides:
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                txt = para.text.strip().lower()
                if len(txt) < 10:
                    continue
                for ws in WEAK:
                    if txt.startswith(ws):
                        weak += 1
                        break
    if weak > 3:
        issues.append(f"  WORD CHOICE: {weak} bullet(s) start with weak phrasing")

    if issues:
        print(f"⚠ DECK-LEVEL issues ({len(issues)}):")
        for iss in issues:
            print(iss)
    else:
        print(f"✓ DECK OK: {len(prs.slides)} slides, {visual_pattern_slides}/{content_slides} visual patterns, "
              f"max {max_consecutive_text} consecutive text")
    return issues


# ═════════════════════════════ BUILD ═════════════════════════════


TEMPLATE_SEARCH = [
    os.path.join(os.getcwd(), "templates", "snowflake_template.pptx"),
    "/Users/dfreriks/Documents/GitHub/cortex-code-skills/skills/snowflake-deck-render/snowflake_template.pptx",
    os.path.expanduser("~/.cortex/skills/900-999_utilities/945-render-pptx/snowflake_template.pptx"),
]


def new_presentation():
    """Load the official template and strip its sample slides."""
    template = next((p for p in TEMPLATE_SEARCH if os.path.isfile(p)), None)
    assert template, "snowflake_template.pptx not found"
    prs = Presentation(template)
    while len(prs.slides) > 0:
        sld = prs.slides._sldIdLst[0]
        rid = (sld.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
               or sld.get('r:id'))
        if rid:
            prs.part.drop_rel(rid)
        prs.slides._sldIdLst.remove(sld)
    return prs
