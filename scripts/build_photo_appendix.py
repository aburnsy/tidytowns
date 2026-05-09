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
APP_PHOTOS = ROOT / "private" / "application-photos-2026"
SITE_PHOTOS = ROOT / "site" / "docs" / "assets" / "map-data" / "photos"
SITE_COMPLETED = ROOT / "site" / "docs" / "completed"
OUTPUT = ROOT / "private" / "application-2026" / "attachments" / "photo-appendix.docx"

GREEN = RGBColor(0x1B, 0x5E, 0x20)


def app_photo(name: str) -> Path:
    return APP_PHOTOS / name


def site_photo(rel: str) -> Path:
    return SITE_PHOTOS / rel


# Heavy-hitter photo set, one or two per project, grouped 6 per A4 page.
# Each tuple: (Path, caption). Caption format: "Section / Project ref / rec — description"
PHOTO_CAPTIONS = [
    # --- Page 1: Streetscape, monument, heritage, adjudicator items ---
    (site_photo("monument/all-ireland-1900-centennial-monument.jpg"),
     "Section 2 — All-Ireland Victory Centennial monument, the village centre anchor"),
    (site_photo("monument/centennial-1900-team-plaque-may-2026.jpg"),
     "Section 1 — 1900 winning panel listed on the monument plaque"),
    (site_photo("cemetery/parking-with-planters-may-2026.jpg"),
     "Section 2 / Project 012 — Cohesive blue trough planters at the cemetery parking layby"),
    (site_photo("transport_museum/gates-may-2026.jpg"),
     "Section 2 / Project 012 — Blue planters at the Transport Museum gates"),
    (site_photo("forge/forge-front-may-2026.jpg"),
     "Section 2 / Project 022 / rec #2 — The forge, replica window subject for Heritage Officer outreach"),
    (app_photo("derelict-property-cemetery-may-2026.jpg"),
     "Section 2 / rec #1 — Derelict property on the L4202 opposite the cemetery; formal report submitted May 2026"),

    # --- Page 2: Bulb programme (Project 047) and Sensory Garden (Projects 018, 048) ---
    (site_photo("approach_west/n75-daffodils-spring-2026.jpg"),
     "Sections 3, 8 / Project 047 — Dutch Master daffodils on the N75 west approach, spring 2026"),
    (site_photo("glen_carraig/crocus-honeybee-closeup-spring-2026.jpg"),
     "Sections 3, 7 / Project 047 — Honeybee on a Ruby Giant crocus at Glen Carraig, spring 2026"),
    (site_photo("cluain_na_seimre/crocuses-spring-2026.jpg"),
     "Sections 3, 7, 8 / Project 047 — 1,500 Ruby Giant crocuses at the Cluain Na Seimre entrance green, March 2026"),
    (site_photo("sensory_garden/timber-gateway-spring-2026.jpg"),
     "Section 3 / Project 018 — Sensory Garden timber gateway after the spring 2026 maintenance blitz"),
    (site_photo("sensory_garden/willow-weaving-spring-2026.jpg"),
     "Section 3 / Project 048 — Patrick H weaving the Sensory Garden's living-willow gateway, March 2026"),
    (app_photo("school-sensory-garden-play-may-2026.jpg"),
     "Sections 3, 4 / rec #7 — Sensory Garden in daily use as the school's outdoor classroom"),

    # --- Page 3: Bog Walk (Project 028) and biodiversity ---
    (site_photo("bog_walk/red-squirrel-path-summer-2025.jpg"),
     "Section 4 / Project 028 — Red Squirrel on the Bog Walk path, summer 2025 (the headline species)"),
    (site_photo("bog_walk/bog-cotton-habitat-summer-2024.jpg"),
     "Section 4 / Project 028 — Bog cotton habitat on the Bog Walk Loop, summer 2024"),
    (site_photo("bog_walk/knapweed-butterfly-summer-2025.jpg"),
     "Section 4 / Project 028 — Small Tortoiseshell on Knapweed, Bog Walk wet meadow, summer 2025"),
    (app_photo("clover-bog-walk-poster-february-2026.jpg"),
     "Section 4 / Project 028 — St Bridget's Day Clover Bog Walk, February 2026"),
    (site_photo("church/bug-hotel-close-may-2026.jpg"),
     "Section 4 / Project 045 — Bug hotel in the St James Church grounds, the existing biodiversity feature"),
    (site_photo("old_road_triangle/under-canopy-may-2026.jpg"),
     "Section 4 — Old Road Triangle under the canopy, deliberate non-intervention biodiversity strategy"),

    # --- Page 4: Sustainability, Tidiness, Residential, Approach Roads ---
    (site_photo("church/guttering-may-2026.jpg"),
     "Section 5 / Project 010 / rec #10 — Cast-iron downpipe at St James Church, candidate water-butt site (TRPS840, Heritage Officer sign-off pending)"),
    (site_photo("monument/mutt-mitt-dispenser-may-2026.jpg"),
     "Section 6 / Project 005 / rec #13 — Mutt-mitt dispenser at the monument, back on the volunteer round"),
    (app_photo("litter-cleanup-haul-april-2026.jpg"),
     "Sections 5, 6 / rec #12 — April 2026 clean-up haul, point-of-collection segregation pilot"),
    (site_photo("fanning_park/hawthorn-blossom-may-2026.jpg"),
     "Section 7 — Flowering Hawthorn anchoring the entrance to Fanning Park, May 2026"),
    (site_photo("approach_south/black-river-willow-alder-may-2026.jpg"),
     "Section 8 — Native Willow and Alder corridor along the Black River, N75 south approach"),
    (site_photo("approach_north/tree-avenue-may-2026.jpg"),
     "Section 8 — Mature deciduous tree avenue framing the Ballyduff Road approach"),
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
    for i, (photo_path, caption) in enumerate(items):
        row, col = divmod(i, 2)
        cell = table.cell(row, col)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
        if not photo_path.exists():
            cell.text = f"[missing: {photo_path.name}]"
            continue
        # Use a unique name in the temp dir to avoid collisions across folders
        resized = tmp_dir / f"{i:02d}_{photo_path.name}"
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
