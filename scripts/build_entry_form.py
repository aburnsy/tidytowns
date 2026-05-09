"""Fill the 2026 SuperValu TidyTowns entry-form Word doc with TMB content.

Loads the trimmed section narratives from `private/application-2026/` and
populates a copy of the official 2026 entry-form template. Run with:

  uv run --with python-docx python scripts/build_entry_form.py

Output:
  applications/2026-TMB-entry-form-filled.docx
"""

import re
from datetime import date
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).parent.parent
TEMPLATE = ROOT / "applications" / "2026-SuperValu-TidyTowns-Entry-Form-English.docx"
APP_DIR = ROOT / "private" / "application-2026"
OUTPUT = ROOT / "applications-2026" / "2026-TMB-entry-form-filled.docx"

GREEN = RGBColor(0x1B, 0x5E, 0x20)

CONTACT = {
    "Name of Town/Area/Village/Island": "Two Mile Borris",
    "Name of Town/Area/Village/Island (Irish)": "Buirios Leith",
    "County": "Tipperary",
    "Region": "South East",
    "Local Authority": "Tipperary County Council",
    "Last Year of Entry": "2025",
    "Organisation Name": "Two Mile Borris Development and Tidy Towns",
    "Contact Name": "Michael Maher",
    "Address": "Loughfield, Two Mile Borris, Thurles, Co. Tipperary, E41 A665",
    "Phone": "086 253 7898",
    "Email": "michael@tmbvillage.com",
    "Internet/Social Media address": (
        "www.tmbvillage.ie  |  https://aburnsy.github.io/tidytowns/  |  Instagram @twomileborristidytowns"
    ),
}

POPULATION = "600"
SIGNED_BY = "Michael Maher"
SIGNED_DATE = date.today().strftime("%d/%m/%Y")

ESTIMATED_LOCATION = (
    "Two Mile Borris is a small village on the N75 in mid-Tipperary, about "
    "5 km east of Thurles and 1 km off the M8 motorway at Junction 5. It can also be approached"
    " from the old National road R639, which runs parallel to the M8 and passes through the nearby "
    "village of Littleton to the South and Urlingford to the North"
)

# Map markdown filename -> section heading prefix to find in the form
SECTIONS = [
    ("02-streetscape.md", "Streetscape"),
    ("03-green-spaces.md", "Green Spaces"),
    ("04-nature-biodiversity.md", "Nature and Biodiversity"),
    ("05-sustainability.md", "Sustainability -"),
    ("06-tidiness.md", "Tidiness and Litter Control"),
    ("07-residential.md", "Residential Streets"),
    ("08-approach-roads.md", "Approach Roads"),
]

# Section 1 (Community) subfield mapping: markdown subheading -> form prompt prefix
COMMUNITY_SUBFIELDS = [
    ("Number involved on your committee", "Number involved in your Committee"),
    ("Number not on committee but who volunteer", "Number not on committee but who volunteer"),
    ("Level of voluntary commitment", "Please indicate level of voluntary commitment"),
    ("Agencies, bodies and businesses supporting our activities", "Please list all the agencies"),
    ("How we communicate with our community", "How do you communicate with your community"),
    ("How we engage with local schools and youth", "How do you engage with your local schools"),
    ("ONE specific project where particular effort was applied since 10 May 2025", "Briefly identify ONE specific project"),
    ("Years entered, and how the community has benefited", "Approximately how many years has your community entered"),
]


def set_cell_text(cell, text: str, bold: bool = False, color: RGBColor | None = None):
    """Replace cell text with a single styled run."""
    cell.text = ""
    para = cell.paragraphs[0]
    run = para.add_run(text)
    run.font.size = Pt(10.5)
    if bold:
        run.bold = True
    if color is not None:
        run.font.color.rgb = color


def add_runs_from_markdown(paragraph, text: str):
    """Add runs to paragraph parsing simple markdown (bold/italic/code/url brackets)."""
    text = text.replace("<https://", "https://").replace(">", "").replace("`", "")
    pattern = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*)")
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            paragraph.add_run(text[pos : m.start()])
        token = m.group(0)
        if token.startswith("**"):
            r = paragraph.add_run(token[2:-2])
            r.bold = True
        else:
            r = paragraph.add_run(token[1:-1])
            r.italic = True
        pos = m.end()
    if pos < len(text):
        paragraph.add_run(text[pos:])
    for run in paragraph.runs:
        if not run.font.size:
            run.font.size = Pt(10.5)


def insert_paragraph_after(paragraph, text: str = "") -> "docx.text.paragraph.Paragraph":
    """Insert a new paragraph immediately after the given paragraph."""
    from docx.text.paragraph import Paragraph

    new_p = OxmlElement("w:p")
    paragraph._element.addnext(new_p)
    para = Paragraph(new_p, paragraph._parent)
    if text:
        add_runs_from_markdown(para, text)
    return para


def delete_paragraph(paragraph):
    elem = paragraph._element
    elem.getparent().remove(elem)


def find_paragraph_by_prefix(doc, prefix: str, start_index: int = 0) -> int:
    for i, p in enumerate(doc.paragraphs[start_index:], start=start_index):
        if p.text.strip().startswith(prefix):
            return i
    return -1


def parse_md_section(md_path: Path) -> list[str]:
    """Strip H1 and return body paragraphs (preserves blank-line separation)."""
    text = md_path.read_text(encoding="utf-8")
    # drop the H1 heading line (e.g., "# 02 — Streetscape & Public Places (80 marks)")
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    body = "\n".join(lines).strip()
    # split into paragraphs on blank lines
    return [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]


def parse_community_md(md_path: Path) -> dict[str, list[str]]:
    """Parse community.md into {subheading: [paragraphs]}."""
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    result: dict[str, list[str]] = {}
    current: str | None = None
    buf: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if current is not None:
                result[current] = _flush_buf(buf)
            current = line[3:].strip()
            buf = []
        elif line.startswith("# ") or (line.startswith("*") and line.endswith("*")):
            continue  # skip H1 and italics-only intro line
        else:
            buf.append(line)
    if current is not None:
        result[current] = _flush_buf(buf)
    return result


def _flush_buf(buf: list[str]) -> list[str]:
    text = "\n".join(buf).strip()
    if not text:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def fill_contact_table(doc):
    table = doc.tables[0]
    for row in table.rows:
        label = row.cells[0].text.strip()
        if label in CONTACT:
            set_cell_text(row.cells[1], CONTACT[label], bold=True, color=GREEN)


def tick_population_category(doc):
    table = doc.tables[1]
    for row in table.rows:
        for cell in row.cells:
            if "B (201 to 1,000)" in cell.text:
                # bold the cell text and prepend a tick
                txt = cell.text
                cell.text = ""
                p = cell.paragraphs[0]
                r = p.add_run("X  " + txt)
                r.bold = True
                r.font.color.rgb = GREEN


def fill_population_field(doc):
    """Replace the population prompt's underscore field with our value."""
    for p in doc.paragraphs:
        if "Please enter your actual population" in p.text:
            # rewrite the paragraph: keep prompt, append value in green/bold
            prompt = p.text.split("_")[0].rstrip()
            for run in list(p.runs):
                run.text = ""
            r1 = p.add_run(prompt + "  ")
            r2 = p.add_run(POPULATION)
            r2.bold = True
            r2.font.color.rgb = GREEN
            r2.font.size = Pt(11)
            return


def fill_estimated_location(doc):
    idx = find_paragraph_by_prefix(doc, "Your adjudicator may not have visited")
    if idx < 0:
        return
    insert_paragraph_after(doc.paragraphs[idx + 1], ESTIMATED_LOCATION)


def fill_signed_date(doc):
    for p in doc.paragraphs:
        if p.text.strip().startswith("Signed (on behalf of entrant)"):
            for run in list(p.runs):
                run.text = ""
            r1 = p.add_run("Signed (on behalf of entrant): ")
            r2 = p.add_run(SIGNED_BY)
            r2.bold = True
            r2.font.color.rgb = GREEN
            r3 = p.add_run("       Date: ")
            r4 = p.add_run(SIGNED_DATE)
            r4.bold = True
            r4.font.color.rgb = GREEN
            return


def fill_community_section(doc):
    parsed = parse_community_md(APP_DIR / "01-community.md")
    for md_heading, form_prompt in COMMUNITY_SUBFIELDS:
        if md_heading not in parsed:
            print(f"  WARN: community subfield not found in md: {md_heading}")
            continue
        idx = find_paragraph_by_prefix(doc, form_prompt)
        if idx < 0:
            print(f"  WARN: form prompt not found: {form_prompt}")
            continue
        # insert each paragraph of the answer after the prompt
        anchor = doc.paragraphs[idx]
        for para_text in reversed(parsed[md_heading]):
            insert_paragraph_after(anchor, para_text)


def fill_marked_sections(doc):
    """For each section heading, delete boilerplate to next heading and insert narrative."""
    # Build the list of section heading indices first (positions are stable
    # because we only modify paragraphs *after* each heading, never before).
    next_section_terminators = ["Mapping your town"]
    section_paragraphs: list[tuple[str, str, int]] = []
    cursor = 0
    for md_filename, form_prefix in SECTIONS:
        idx = find_paragraph_by_prefix(doc, form_prefix, start_index=cursor)
        if idx < 0:
            print(f"  WARN: section heading not found: {form_prefix}")
            continue
        section_paragraphs.append((md_filename, form_prefix, idx))
        cursor = idx + 1

    # Process sections in reverse so paragraph indices for earlier sections
    # remain valid as we delete blocks of paragraphs from later sections.
    for i, (md_filename, form_prefix, _idx) in enumerate(reversed(section_paragraphs)):
        # find current index (re-scan because earlier deletions may shift)
        idx = find_paragraph_by_prefix(doc, form_prefix)
        if idx < 0:
            continue
        # find next-section heading
        next_idx = None
        for next_prefix in [s[1] for s in section_paragraphs[len(section_paragraphs) - len(section_paragraphs) + (len(section_paragraphs) - i):]] + next_section_terminators:
            next_idx_try = find_paragraph_by_prefix(doc, next_prefix, start_index=idx + 1)
            if next_idx_try > 0:
                next_idx = next_idx_try
                break
        if next_idx is None:
            print(f"  WARN: no terminator found for section {form_prefix}")
            continue
        # delete paragraphs between idx and next_idx (exclusive both)
        to_delete = list(doc.paragraphs[idx + 1 : next_idx])
        for p in to_delete:
            delete_paragraph(p)
        # insert section content
        anchor = doc.paragraphs[idx]
        paras = parse_md_section(APP_DIR / md_filename)
        for para_text in reversed(paras):
            insert_paragraph_after(anchor, para_text)


def main():
    if not TEMPLATE.exists():
        raise SystemExit(f"Template not found: {TEMPLATE}")
    doc = Document(str(TEMPLATE))
    print(f"Loaded template: {TEMPLATE.name}")

    fill_contact_table(doc)
    print("  contact table OK")

    tick_population_category(doc)
    fill_population_field(doc)
    print("  population OK")

    fill_estimated_location(doc)
    print("  estimated location OK")

    fill_signed_date(doc)
    print("  signature/date OK")

    fill_community_section(doc)
    print("  Community subfields OK")

    fill_marked_sections(doc)
    print("  Marked sections OK")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT))
    size_kb = OUTPUT.stat().st_size // 1024
    print(f"\nOK: {OUTPUT.relative_to(ROOT)} ({size_kb} KB)")


if __name__ == "__main__":
    main()
