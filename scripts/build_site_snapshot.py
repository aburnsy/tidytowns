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

import base64
import html
import re
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "site" / "docs"
OUT_DIR = ROOT / "applications-2026"
PHOTO_DIR = ROOT / "private" / "application-photos-2026"
OUTPUT = OUT_DIR / "project-tracker-snapshot.pdf"
SITE_URL = "https://aburnsy.github.io/tidytowns"
COVER_PHOTO = PHOTO_DIR / "village-aerial-sunset-spring-2025.jpg"

BROWSER_CANDIDATES = [
    # Chrome first - Edge headless --print-to-pdf is unreliable on this machine
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


def find_browser() -> Path:
    for p in BROWSER_CANDIDATES:
        if p.exists():
            return p
    for name in ("chrome", "msedge"):
        found = shutil.which(name)
        if found:
            return Path(found)
    raise SystemExit("ERROR: Chrome or Edge not found.")


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

    subdir = p.get("_subdir", "projects")
    folder = p.get("_folder", "")
    project_url = f"{SITE_URL}/{subdir}/{folder}/" if folder else SITE_URL

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
        <div class="project-title"><a href="{html.escape(project_url)}"><span class="project-id">{pid}</span> {title}</a></div>
        <div class="project-badges">{''.join(badges)}</div>
      </div>
      {f'<div class="project-status"><strong>Status:</strong> {status}</div>' if status else ''}
      {f'<div class="project-cost"><strong>Cost:</strong> {cost}</div>' if cost else ''}
      {f'<div class="project-summary">{summary}</div>' if summary else ''}
    </div>
    """


def render_section(title: str, projects: list, lead: str = "", page_break: bool = False) -> str:
    if not projects:
        return ""
    rows = "\n".join(render_project_row(p) for p in projects)
    lead_html = f'<p class="section-lead">{html.escape(lead)}</p>' if lead else ""
    cls = ' class="page-break-before"' if page_break else ""
    return f"""
    <section{cls}>
      <h2>{html.escape(title)}</h2>
      {lead_html}
      {rows}
    </section>
    """


def cover_photo_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{data}"


def _delivery_year_key(value):
    if isinstance(value, list):
        value = value[0] if value else ""
    try:
        return int(str(value).strip())
    except (ValueError, AttributeError):
        return 9999  # missing/unsortable years go last


def sort_by_delivery_year(projects: list) -> list:
    return sorted(projects, key=lambda p: (_delivery_year_key(p.get("delivery_year", "")), p.get("_id", "")))


CSS = """
@page { size: A4; margin: 16mm 14mm 18mm 14mm; }
body {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 9.5pt;
  line-height: 1.4;
  color: #222;
}
.cover-page {
  page-break-after: always;
  text-align: center;
  padding-top: 4mm;
}
.cover-page h1 {
  font-size: 26pt;
  color: #1B5E20;
  margin: 0 0 4pt 0;
  letter-spacing: 0.5pt;
}
.cover-page .subtitle {
  font-size: 13pt;
  color: #444;
  margin-bottom: 14pt;
}
.cover-hero {
  width: 100%;
  max-height: 130mm;
  object-fit: cover;
  border-radius: 3pt;
  margin: 0 0 14pt 0;
  box-shadow: 0 1pt 3pt rgba(0,0,0,0.18);
}
.cover-page .meta {
  font-size: 10pt;
  color: #666;
  margin-top: 10pt;
}
.intro {
  background: #F1F8E9;
  border-left: 4px solid #1B5E20;
  padding: 12pt 14pt;
  margin: 0 6mm 0 6mm;
  font-size: 10.5pt;
  line-height: 1.5;
  text-align: left;
  color: #222;
}
section { margin-bottom: 10pt; }
section.page-break-before { page-break-before: always; }
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
a { color: #1B5E20; text-decoration: none; }
.project-title a { color: inherit; }
.project-title a:hover { text-decoration: underline; }
.cover .meta a, .intro a { color: #1B5E20; text-decoration: underline; }
"""


def build_html(active, completed, future):
    today = date.today().isoformat()
    site_link = f'<a href="{SITE_URL}/">{SITE_URL.replace("https://", "")}/</a>'
    intro = (
        "This document is a printable snapshot of the live Two Mile Borris TidyTowns "
        f"project tracker at {site_link}. The live site is the "
        "formal multi-year plan; this PDF is included as Attachment 2 of the 2026 "
        "submission so the adjudicator has a single static index of all projects, "
        "their status, benefit and cost. Each project title in the following pages "
        "links straight to its full page on the tracker, with supporting evidence "
        "and updates."
    )
    photo_uri = cover_photo_data_uri(COVER_PHOTO)
    photo_html = f'<img class="cover-hero" src="{photo_uri}" alt="Two Mile Borris at sunset">' if photo_uri else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Two Mile Borris TidyTowns: Project Tracker Snapshot</title>
<style>{CSS}</style>
</head>
<body>
<div class="cover-page">
  <h1>Two Mile Borris TidyTowns</h1>
  <div class="subtitle">Project Tracker, 3 to 5 Year Plan</div>
  {photo_html}
  <div class="intro">{intro}</div>
  <div class="meta">Snapshot generated {today} &middot; Live tracker: <a href="{SITE_URL}/">{SITE_URL.replace("https://", "")}/</a></div>
</div>
{render_section("Active Projects", active, "Currently being delivered or scheduled within the current planning window.", page_break=True)}
{render_section("Future Projects", future, "Multi-year ambitions on the public tracker, captured here as forward-look.", page_break=True)}
{render_section("Completed Projects", completed, "Projects delivered, captured for the application record.", page_break=True)}
</body>
</html>
"""


def html_to_pdf(browser: Path, html_str: str, dst: Path):
    html_str = strip_em_dashes(html_str)
    dst = dst.resolve()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / "snapshot.html"
        html_path.write_text(html_str, encoding="utf-8")
        url = html_path.resolve().as_uri()
        user_data_dir = tmp_path / "browser-profile"
        subprocess.run(
            [
                str(browser),
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--user-data-dir={user_data_dir}",
                f"--print-to-pdf={dst}",
                url,
            ],
            check=True,
            capture_output=True,
        )


def main():
    browser = find_browser()
    print(f"Using browser at: {browser}")
    active = sort_by_delivery_year(scan_dir("projects"))
    completed = sort_by_delivery_year(scan_dir("completed"))
    future = sort_by_delivery_year(scan_dir("future"))
    print(f"Active: {len(active)}, Completed: {len(completed)}, Future: {len(future)}")
    html_str = build_html(active, completed, future)
    html_to_pdf(browser, html_str, OUTPUT)
    print(f"OK: -> {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
