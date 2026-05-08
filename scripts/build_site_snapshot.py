"""Build a printable PDF snapshot of the public project tracker.

This is attachment #2 in the 2026 TidyTowns submission: the live site at
https://aburnsy.github.io/tidytowns/ acts as the formal multi-year plan, and
this PDF gives the adjudicator a static printable index of all projects
(active, completed, future) for the application bundle.

Reads frontmatter from site/docs/projects/, completed/, future/ and renders
a single tabular HTML document, then prints to PDF via Edge headless.

Run with:
  uv run python scripts/build_site_snapshot.py
"""

import html
import re
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "site" / "docs"
ATTACH_DIR = ROOT / "private" / "application-2026" / "attachments"
OUTPUT = ATTACH_DIR / "project-tracker-snapshot.pdf"

EDGE_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


def find_edge() -> Path:
    for p in EDGE_CANDIDATES:
        if p.exists():
            return p
    found = shutil.which("msedge")
    if found:
        return Path(found)
    raise SystemExit("ERROR: Microsoft Edge not found.")


def read_frontmatter(filepath: Path):
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    fm_text = text[3:end].strip()
    body = text[end + 3 :].strip()
    meta = {}
    current_key = None
    current_list = None
    for line in fm_text.splitlines():
        if line.startswith("  - ") and current_key:
            if current_list is None:
                current_list = []
            val = line[4:].strip().strip('"').strip("'")
            current_list.append(val)
            meta[current_key] = current_list
            continue
        m = re.match(r"^(\w[\w_]*):\s*(.*)", line)
        if m:
            current_key = m.group(1)
            current_list = None
            val = m.group(2).strip().strip('"').strip("'")
            if val == "" or val == "[]":
                meta[current_key] = []
            elif val.startswith("[") and val.endswith("]"):
                items = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
                meta[current_key] = items
                current_list = items
            else:
                meta[current_key] = val
    return meta, body


def first_paragraph(body: str) -> str:
    body = re.sub(r"^#.*$", "", body, flags=re.MULTILINE).strip()
    body = re.sub(r"^##\s+Description\s*$", "", body, flags=re.MULTILINE).strip()
    parts = [p.strip() for p in body.split("\n\n") if p.strip()]
    for p in parts:
        if p.startswith("#") or p.startswith("```"):
            continue
        clean = re.sub(r"\s+", " ", p)
        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", clean)
        clean = re.sub(r"\*(.+?)\*", r"\1", clean)
        clean = re.sub(r"`(.+?)`", r"\1", clean)
        clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
        if len(clean) > 320:
            clean = clean[:320].rsplit(" ", 1)[0] + "…"
        return clean
    return ""


def scan_dir(subdir: str):
    base = DOCS / subdir
    if not base.exists():
        return []
    projects = []
    for proj_dir in sorted(base.iterdir()):
        if not proj_dir.is_dir() or not re.match(r"^\d{3}-", proj_dir.name):
            continue
        index_file = proj_dir / "index.md"
        if not index_file.exists():
            continue
        meta, body = read_frontmatter(index_file)
        meta["_folder"] = proj_dir.name
        meta["_id"] = proj_dir.name[:3]
        meta["_summary"] = first_paragraph(body)
        meta["_subdir"] = subdir
        projects.append(meta)
    return projects


def strip_em_dashes(text: str) -> str:
    return text.replace("—", ", ").replace("&mdash;", ", ")


def fmt(value) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, list):
        return strip_em_dashes(", ".join(value))
    return strip_em_dashes(str(value))


def render_project_row(p: dict) -> str:
    pid = html.escape(p.get("_id", ""))
    title = html.escape(fmt(p.get("title", p.get("_folder", ""))))
    status = html.escape(fmt(p.get("status", "")))
    benefit = html.escape(fmt(p.get("benefit", "")))
    cost = html.escape(fmt(p.get("cost_estimate", "")))
    delivery = html.escape(fmt(p.get("delivery_year", "")))
    tags = html.escape(fmt(p.get("tags", "")))
    summary = html.escape(strip_em_dashes(p.get("_summary", "")))

    badges = []
    if benefit:
        badges.append(f'<span class="badge benefit-{benefit.lower()}">Benefit: {benefit}</span>')
    if delivery:
        badges.append(f'<span class="badge year">{delivery}</span>')
    if tags:
        badges.append(f'<span class="badge tags">{tags}</span>')

    return f"""
    <div class="project">
      <div class="project-head">
        <div class="project-title"><span class="project-id">{pid}</span> {title}</div>
        <div class="project-badges">{''.join(badges)}</div>
      </div>
      {f'<div class="project-status"><strong>Status:</strong> {status}</div>' if status else ''}
      {f'<div class="project-cost"><strong>Cost:</strong> {cost}</div>' if cost else ''}
      {f'<div class="project-summary">{summary}</div>' if summary else ''}
    </div>
    """


def render_section(title: str, projects: list, lead: str = "") -> str:
    if not projects:
        return ""
    rows = "\n".join(render_project_row(p) for p in projects)
    lead_html = f'<p class="section-lead">{html.escape(lead)}</p>' if lead else ""
    return f"""
    <section>
      <h2>{html.escape(title)}</h2>
      {lead_html}
      {rows}
    </section>
    """


CSS = """
@page { size: A4; margin: 16mm 14mm 18mm 14mm; }
body {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 9.5pt;
  line-height: 1.4;
  color: #222;
}
.cover {
  text-align: center;
  margin-bottom: 18pt;
  padding-bottom: 14pt;
  border-bottom: 2px solid #1B5E20;
}
.cover h1 {
  font-size: 22pt;
  color: #1B5E20;
  margin: 0 0 6pt 0;
}
.cover .subtitle { font-size: 11pt; color: #444; }
.cover .meta { font-size: 9pt; color: #666; margin-top: 6pt; }
.intro {
  background: #F1F8E9;
  border-left: 4px solid #1B5E20;
  padding: 10pt 12pt;
  margin-bottom: 14pt;
  font-size: 9.5pt;
}
section { margin-bottom: 10pt; }
section h2 {
  font-size: 14pt;
  color: #1B5E20;
  border-bottom: 1px solid #C8E6C9;
  padding-bottom: 4pt;
  margin: 12pt 0 6pt 0;
  page-break-after: avoid;
}
.section-lead {
  font-size: 9.5pt;
  color: #555;
  font-style: italic;
  margin-bottom: 6pt;
}
.project {
  border: 1px solid #DDD;
  border-radius: 3pt;
  padding: 7pt 9pt;
  margin-bottom: 6pt;
  page-break-inside: avoid;
}
.project-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 6pt;
  margin-bottom: 3pt;
}
.project-title {
  font-weight: 600;
  color: #1B5E20;
  font-size: 10.5pt;
}
.project-id {
  display: inline-block;
  background: #1B5E20;
  color: white;
  font-size: 8.5pt;
  padding: 1pt 5pt;
  border-radius: 2pt;
  margin-right: 4pt;
  font-weight: 700;
}
.project-badges { display: inline; }
.badge {
  display: inline-block;
  font-size: 8pt;
  padding: 1pt 5pt;
  border-radius: 2pt;
  margin-left: 3pt;
  background: #ECEFF1;
  color: #455A64;
}
.badge.benefit-high { background: #C8E6C9; color: #1B5E20; }
.badge.benefit-medium { background: #FFF9C4; color: #827717; }
.badge.benefit-low { background: #ECEFF1; color: #455A64; }
.badge.year { background: #E3F2FD; color: #0D47A1; }
.project-status, .project-cost { font-size: 9pt; margin-top: 2pt; }
.project-summary { font-size: 9pt; margin-top: 4pt; color: #444; }
strong { color: #1B5E20; }
"""


def build_html(active, completed, future):
    today = date.today().isoformat()
    intro = (
        "This document is a printable snapshot of the live Two Mile Borris TidyTowns "
        "project tracker at https://aburnsy.github.io/tidytowns/. The live site is the "
        "formal multi-year plan; this PDF is included as Attachment 2 of the 2026 "
        "submission so the adjudicator has a single static index of all projects, "
        "their status, benefit and cost. The live site holds the full project pages, "
        "supporting evidence and updates."
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Two Mile Borris TidyTowns: Project Tracker Snapshot</title>
<style>{CSS}</style>
</head>
<body>
<div class="cover">
  <h1>Two Mile Borris TidyTowns</h1>
  <div class="subtitle">Project Tracker, 3 to 5 Year Plan</div>
  <div class="meta">Snapshot generated {today} &middot; Live tracker: aburnsy.github.io/tidytowns</div>
</div>
<div class="intro">{html.escape(intro)}</div>
{render_section("Active Projects", active, "Currently being delivered or scheduled within the current planning window.")}
{render_section("Completed Projects", completed, "Projects delivered, captured for the application record.")}
{render_section("Future Projects", future, "Multi-year ambitions on the public tracker, captured here as forward-look.")}
</body>
</html>
"""


def html_to_pdf(edge: Path, html_str: str, dst: Path):
    html_str = strip_em_dashes(html_str)
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "snapshot.html"
        html_path.write_text(html_str, encoding="utf-8")
        url = html_path.resolve().as_uri()
        subprocess.run(
            [
                str(edge),
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={dst}",
                url,
            ],
            check=True,
            capture_output=True,
        )


def main():
    edge = find_edge()
    print(f"Using Edge at: {edge}")
    active = scan_dir("projects")
    completed = scan_dir("completed")
    future = scan_dir("future")
    print(f"Active: {len(active)}, Completed: {len(completed)}, Future: {len(future)}")
    html_str = build_html(active, completed, future)
    html_to_pdf(edge, html_str, OUTPUT)
    print(f"OK: -> {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
