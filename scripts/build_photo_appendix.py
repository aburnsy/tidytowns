"""Build the photo-appendix Word document for the 2026 TidyTowns submission.

Per the 2026 booklet (page 5, point 13), photographs may be supplied as
"an appendix to the form in a WORD document" with up to six per A4 page,
each titled so the adjudicator knows what project it refers to.

This script reads photos from `private/application-photos-2026/`, looks up
captions in this file (PHOTO_CAPTIONS below) and writes a Word doc with
six photos per A4 page in a 2-column x 3-row table.

Run with:
  uv run --with python-docx --with pillow python scripts/build_photo_appendix.py
"""

import tempfile
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

# Resize photos to this max long-edge before embedding. At 8.5cm x 6cm display
# size and ~200 DPI, ~700px is enough; we keep 1200px for adjudicator zoom.
EMBED_MAX_PX = 1200
EMBED_JPEG_QUALITY = 82

ROOT = Path(__file__).parent.parent
PHOTO_DIR = ROOT / "private" / "application-photos-2026"
OUTPUT = ROOT / "private" / "application-2026" / "attachments" / "photo-appendix.docx"

GREEN = RGBColor(0x1B, 0x5E, 0x20)

# Photos in display order. Each tuple: (filename, caption).
# Caption format: "Section / Project ref — description, date if relevant"
PHOTO_CAPTIONS = [
    (
        "village-aerial-sunset-spring-2025.jpg",
        "Two Mile Borris at sunset, spring 2025 — village core context",
    ),
    (
        "village-aerial-daytime-spring-2025.jpg",
        "Two Mile Borris from the air, spring 2025 — village layout",
    ),
    (
        "school-visit-monument-may-2026.jpg",
        "Sections 1, 2, 4 — Two Mile Borris NS at the All-Ireland Victory Centennial monument, May 2026",
    ),
    (
        "school-sensory-garden-play-may-2026.jpg",
        "Sections 3, 4 / Projects 018 and 048 — Sensory Garden in daily school use as outdoor classroom, May 2026",
    ),
    (
        "school-sensory-garden-paving-may-2026.jpg",
        "Section 3 / Project 018 — Sensory Garden paving, school visit May 2026",
    ),
    (
        "sensory-garden-gateway-willow-march-2026.jpg",
        "Section 3 / Project 048 — Sensory Garden living-willow gateway after re-weave, March 2026",
    ),
    (
        "sensory-garden-willow-weaving-march-2026.jpg",
        "Section 3 / Project 048 — Patrick H reweaving the Sensory Garden willow gateway, March 2026",
    ),
    (
        "school-litter-pick-entrance-may-2026.jpg",
        "Section 4 / Green Schools — Two Mile Borris NS litter pick at the school entrance, May 2026",
    ),
    (
        "litter-pick-volunteers-n75-april-2026.jpg",
        "Sections 6, 8 — April 2026 clean-up volunteers on the N75 approach",
    ),
    (
        "litter-pick-volunteers-hedgerow.jpg",
        "Sections 6, 8 — April 2026 clean-up volunteers along approach-road hedgerow",
    ),
    (
        "litter-pick-trailer-collection-april-2026.jpg",
        "Section 6 — April 2026 clean-up trailer collection point",
    ),
    (
        "litter-cleanup-haul-april-2026.jpg",
        "Sections 5, 6 — April 2026 clean-up full haul, segregation pilot (rec #12)",
    ),
    (
        "derelict-property-cemetery-may-2026.jpg",
        "Section 2 / rec #1 — Derelict property on the L4202 opposite the cemetery, formal report submitted May 2026",
    ),
    (
        "clover-bog-walk-poster-february-2026.jpg",
        "Section 4 / Project 028 — St Bridget's Day Clover Bog Walk poster, February 2026",
    ),
]

# A4 portrait usable area at 1.5cm margins is ~18cm wide x 24.7cm tall.
# 2 columns x 3 rows = each cell is ~9cm x ~8.2cm.
# Reserve ~1.2cm of cell height for the caption, so photos are 9cm x ~7cm.
PHOTO_TARGET_W_CM = 8.5
PHOTO_TARGET_H_CM = 6.0


def set_a4_portrait(doc: Document):
    section = doc.sections[0]
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.2)
    section.bottom_margin = Cm(1.2)
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)


def add_title_page(doc: Document):
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Two Mile Borris TidyTowns 2026")
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = GREEN

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = subtitle.add_run("Photograph Appendix")
    sub_run.font.size = Pt(14)
    sub_run.font.color.rgb = GREEN

    intro = doc.add_paragraph()
    intro.alignment = WD_ALIGN_PARAGRAPH.LEFT
    intro_run = intro.add_run(
        "Photographs supporting the 2026 entry-form sections, arranged six per A4 page. "
        "Each photo is titled with the relevant section number(s) and project reference "
        "so the adjudicator can match the visual to the narrative. The full live record "
        "of every project, with additional photos and updates as the year progresses, "
        "sits on the public tracker at https://aburnsy.github.io/tidytowns/."
    )
    intro_run.font.size = Pt(10.5)


def fit_photo(path: Path):
    """Return (width_cm, height_cm) sized to fit within target box, preserving aspect ratio."""
    with Image.open(path) as im:
        w_px, h_px = im.size
    aspect = w_px / h_px
    target_aspect = PHOTO_TARGET_W_CM / PHOTO_TARGET_H_CM
    if aspect > target_aspect:
        # photo is wider than the box, fit to width
        return PHOTO_TARGET_W_CM, PHOTO_TARGET_W_CM / aspect
    return PHOTO_TARGET_H_CM * aspect, PHOTO_TARGET_H_CM


def resize_for_embed(src: Path, dst: Path):
    """Save a resized copy of src to dst, with the long edge capped at EMBED_MAX_PX."""
    with Image.open(src) as im:
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGB")
        im.thumbnail((EMBED_MAX_PX, EMBED_MAX_PX), Image.LANCZOS)
        im.save(dst, format="JPEG", quality=EMBED_JPEG_QUALITY, optimize=True)


def add_photo_page(doc: Document, items: list, page_index: int, tmp_dir: Path):
    if page_index > 0:
        doc.add_page_break()
    table = doc.add_table(rows=3, cols=2)
    table.autofit = False
    table.allow_autofit = False
    for col in table.columns:
        for cell in col.cells:
            cell.width = Cm(9.0)
    for i, (filename, caption) in enumerate(items):
        row, col = divmod(i, 2)
        cell = table.cell(row, col)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
        photo_path = PHOTO_DIR / filename
        if not photo_path.exists():
            cell.text = f"[missing: {filename}]"
            continue
        resized = tmp_dir / filename
        resize_for_embed(photo_path, resized)
        cell.text = ""
        photo_para = cell.paragraphs[0]
        photo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = photo_para.add_run()
        w_cm, h_cm = fit_photo(resized)
        run.add_picture(str(resized), width=Cm(w_cm), height=Cm(h_cm))
        cap_para = cell.add_paragraph()
        cap_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap_run = cap_para.add_run(caption)
        cap_run.font.size = Pt(8.5)
        cap_run.italic = True


def main():
    doc = Document()
    set_a4_portrait(doc)
    add_title_page(doc)
    items = list(PHOTO_CAPTIONS)
    pages = [items[i : i + 6] for i in range(0, len(items), 6)]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for i, page_items in enumerate(pages):
            add_photo_page(doc, page_items, i, tmp_dir)
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        doc.save(OUTPUT)
    size_kb = OUTPUT.stat().st_size // 1024
    print(f"OK: {OUTPUT.relative_to(ROOT)} ({size_kb} KB, {len(items)} photos on {len(pages)} pages)")


if __name__ == "__main__":
    main()
