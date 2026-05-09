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
OUTPUT = ROOT / "applications-2026" / "photo-appendix.docx"

GREEN = RGBColor(0x1B, 0x5E, 0x20)


def app_photo(name: str) -> Path:
    return APP_PHOTOS / name


def site_photo(rel: str) -> Path:
    return SITE_PHOTOS / rel


# Heavy-hitter photo set, six photos per A4 page.
# Caption format: "Section / Project ref / rec - description" (no em-dashes).
PHOTO_CAPTIONS = [
    # --- Page 1: Village heart, monument, heritage, cemetery, derelict ---
    (app_photo("village-aerial-daytime-spring-2025.jpg"),
     "Cover - Two Mile Borris from the air, spring 2025 (village core, school and Sensory Garden centre frame)"),
    (site_photo("monument/monument-wall-flowers-may-2026.jpg"),
     "Section 2 - All-Ireland Victory Centennial monument with the 2026 flower bed in the foreground"),
    (site_photo("monument/flower-bed-portrait-may-2026.jpg"),
     "Section 2 / Project 012 - Close-up of the monument flower bed in full bloom, May 2026"),
    (site_photo("cemetery/parking-with-planters-may-2026.jpg"),
     "Section 2 / Project 012 - Cohesive blue trough planters at the cemetery parking layby"),
    (site_photo("new_cemetery_entrance/entrance-may-2026.jpg"),
     "Section 1 - New graveyard entrance stonework, completed 2025 (committee contributed EUR1,000 and attended Turning of the Sod, February 2025)"),
    (app_photo("derelict-property-cemetery-may-2026.jpg"),
     "Section 2 / rec #1 - Derelict property on the L4202 opposite the cemetery; formal report submitted to the council in May 2026"),

    # --- Page 2: Bulb programme (Project 047) HERO and the dramatic spread ---
    (site_photo("seating_area/alliums-roadside-may-2026.jpg"),
     "Section 1 / Section 3 / Project 047 - Allium and crocus display framing the village seating area, May 2026 (the lead bulb-programme image)"),
    (site_photo("approach_west/n75-daffodils-spring-2026.jpg"),
     "Sections 3, 8 / Project 047 - Dutch Master daffodils on the N75 west approach, spring 2026"),
    (site_photo("cluain_na_seimre/crocuses-spring-2026.jpg"),
     "Sections 3, 7, 8 / Project 047 - 1,500 Ruby Giant crocuses at the Cluain Na Seimre entrance green, March 2026"),
    (site_photo("glen_carraig/crocus-honeybee-closeup-spring-2026.jpg"),
     "Sections 3, 7 / Project 047 - Honeybee on a Ruby Giant crocus at Glen Carraig, spring 2026"),
    (site_photo("glen_carraig/daffodils-stone-wall-spring-2026.jpg"),
     "Sections 3, 7 / Project 047 - Dutch Master daffodils along the Glen Carraig limestone wall, spring 2026"),
    (site_photo("glen_carraig/alliums-stone-wall-may-2026.jpg"),
     "Sections 3, 7 / Project 047 - Alliums along the Glen Carraig limestone wall, May 2026"),

    # --- Page 3: Bulbs in bloom + wildflower areas ---
    (site_photo("seating_area/wildflowers-gravel-may-2026.jpg"),
     "Section 3 - Wildflowers on the gravel at the village seating area, May 2026"),
    (site_photo("leighton_manor/alliums-wildflowers-may-2026.jpg"),
     "Sections 3, 7 / Project 047 - Alliums in the Leighton Manor wildflower strip, May 2026"),
    (site_photo("leighton_manor/wildflower-strip-may-2026.jpg"),
     "Sections 3, 7 - Leighton Manor roadside wildflower strip, May 2026"),
    (site_photo("monument/wildflower-strip-main-road-may-2026.jpg"),
     "Sections 2, 3 - Wildflower strip on the main road at the monument area, May 2026"),
    (site_photo("castle_park/wildflower-border-may-2026.jpg"),
     "Section 7 - Wildflower border at Castle Park, May 2026"),
    (site_photo("old_road_triangle/bluebells-and-nettles-may-2026.jpg"),
     "Section 4 - Bluebells and nettles in the Old Road Triangle, deliberate non-intervention area, May 2026"),

    # --- Page 4: Committee at work + April clean-up + community days ---
    (app_photo("cleanup-n75-volunteers-april-2026.jpg"),
     "Sections 1, 6 / rec #12 - Committee volunteers in hi-vis on the N75 approach during the April 2026 clean-up programme"),
    (app_photo("litter-cleanup-haul-april-2026.jpg"),
     "Sections 5, 6 / rec #12 - April 2026 clean-up haul, the first run of the point-of-collection segregation pilot"),
    (app_photo("litter-pick-trailer-collection-april-2026.jpg"),
     "Sections 1, 6 - Trailer collection of bagged waste at the end of an April 2026 clean-up evening"),
    (app_photo("litter-pick-volunteers-hedgerow.jpg"),
     "Sections 1, 6 - Volunteers working a hedgerow stretch on a 2026 village litter pick"),
    (app_photo("april-litter-pick-flyer-2026.jpg"),
     "Section 1 / rec #12 - April Community Litter Pick flyer, pushed out across Parents Association comms, residents-association chats, Instagram and email"),
    (app_photo("sensory-garden-willow-weaving-march-2026.jpg"),
     "Section 3 / Project 048 - Patrick H weaving the Sensory Garden's living-willow gateway, March 2026"),

    # --- Page 5: Sensory Garden + school + community life ---
    (site_photo("sensory_garden/pergola-may-2026.jpg"),
     "Section 3 / Project 018 - Sensory Garden timber pergola, freshly oiled in the spring 2026 maintenance blitz"),
    (site_photo("sensory_garden/timber-gateway-spring-2026.jpg"),
     "Section 3 / Project 048 - Living-willow gateway at the Sensory Garden, freshly rewoven in spring 2026"),
    (site_photo("sensory_garden/volunteer-wooden-throne-april-2026.jpg"),
     "Section 3 - Volunteer-built wooden throne in the Sensory Garden, April 2026"),
    (app_photo("school-sensory-garden-play-may-2026.jpg"),
     "Sections 3, 4 / rec #7 - Sensory Garden in daily use as the school's outdoor classroom"),
    (app_photo("wellie-walk-joan-poster-december-2025.jpg"),
     "Section 1 - Joan's Wellie Walk and Auction, St Stephen's Day 2025, in memory of committee member Joan O'Dwyer; takings go to the Christmas Lights Committee"),
    (app_photo("clover-bog-walk-poster-february-2026.jpg"),
     "Sections 1, 4 / Project 028 - Annual St Bridget's Day Clover Bog Walk, February 2026 (EUR1,000 of the 2025 takings went to the graveyard development)"),

    # --- Page 6: Bog Walk biodiversity + heritage forge + approach roads + planters ---
    (site_photo("bog_walk/red-squirrel-path-summer-2025.jpg"),
     "Section 4 / Project 028 - Red Squirrel on the Bog Walk path, summer 2025 (the headline species)"),
    (site_photo("bog_walk/bog-cotton-habitat-summer-2024.jpg"),
     "Section 4 / Project 028 - Bog cotton habitat on the Bog Walk Loop, summer 2024"),
    (site_photo("bog_walk/knapweed-butterfly-summer-2025.jpg"),
     "Section 4 / Project 028 - Small Tortoiseshell on Knapweed, Bog Walk wet meadow, summer 2025"),
    (site_photo("church/bug-hotel-close-may-2026.jpg"),
     "Section 4 / Project 045 - Bug hotel in the St James Church grounds, the existing biodiversity feature"),
    (site_photo("forge/forge-front-may-2026.jpg"),
     "Section 2 / Project 022 / rec #2 - The forge, replica window subject for Heritage Officer outreach"),
    (site_photo("approach_north/tree-avenue-may-2026.jpg"),
     "Section 8 - Mature deciduous tree avenue framing the Ballyduff Road approach"),

    # --- Page 7: Streetscape closers, sustainability, residential, southern approach ---
    (site_photo("monument/mutt-mitt-dispenser-may-2026.jpg"),
     "Section 6 / Project 005 / rec #13 - Mutt-mitt dispenser at the monument, back on the volunteer round"),
    (site_photo("church/guttering-may-2026.jpg"),
     "Section 5 / Project 010 / rec #10 - Cast-iron downpipe at St James Church, candidate water-butt site (TRPS840, Heritage Officer sign-off pending)"),
    (site_photo("meadow_brook/planter-in-flower-summer-2025.jpg"),
     "Sections 2, 7 / Project 012 - Seamus-built blue trough planter in full summer flower at Meadow Brook"),
    (site_photo("fanning_park/hawthorn-blossom-may-2026.jpg"),
     "Section 7 - Flowering Hawthorn anchoring the entrance to Fanning Park, May 2026"),
    (site_photo("approach_south/black-river-willow-alder-may-2026.jpg"),
     "Section 8 - Native Willow and Alder corridor along the Black River, N75 south approach"),
    (site_photo("old_road_triangle/under-canopy-may-2026.jpg"),
     "Section 4 - Old Road Triangle under the canopy, deliberate non-intervention biodiversity strategy"),
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
        "so the adjudicator can match the visual to the narrative. The lead bulb-programme "
        "image (page 2, top-left) is the allium and crocus display at the village seating "
        "area, the most dramatic single image of the autumn 2025 to spring 2026 planting. "
        "The full live record of every project, with additional photos and updates as the "
        "year progresses, sits on the public tracker at https://aburnsy.github.io/tidytowns/."
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
