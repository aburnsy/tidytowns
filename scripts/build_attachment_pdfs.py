"""Convert markdown attachments to clean PDFs for the 2026 TidyTowns submission.

Uses Microsoft Edge in headless mode to print rendered HTML to PDF. Edge ships
on every Windows 11 machine, so no Python PDF library / GTK runtime is needed.

Run with:
  uv run --with markdown-it-py python scripts/build_attachment_pdfs.py
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).parent.parent
APP_DIR = ROOT / "private" / "application-2026"
ATTACH_DIR = APP_DIR / "attachments"

SOURCES = [
    (APP_DIR / "guiding-principles.md", ATTACH_DIR / "guiding-principles.pdf", "Two Mile Borris TidyTowns 2026: Guiding Principles"),
    (ATTACH_DIR / "species-planting-note.md", ATTACH_DIR / "species-planting-note.pdf", "Two Mile Borris TidyTowns 2026: Planting and Species Note"),
]

BROWSER_CANDIDATES = [
    # Chrome first - Edge headless --print-to-pdf is unreliable on this machine
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]

CSS_RULES = """
@page { size: A4; margin: 18mm 16mm 22mm 16mm; }
body {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.5;
  color: #222;
  max-width: 100%;
}
h1 {
  font-size: 20pt;
  color: #1B5E20;
  border-bottom: 2px solid #1B5E20;
  padding-bottom: 6px;
  margin-bottom: 14pt;
}
h2 {
  font-size: 13pt;
  color: #1B5E20;
  margin-top: 18pt;
  margin-bottom: 6pt;
  page-break-after: avoid;
}
h3 {
  font-size: 11.5pt;
  color: #2E7D32;
  margin-top: 12pt;
  margin-bottom: 4pt;
  page-break-after: avoid;
}
p { margin: 0 0 8pt 0; }
ol, ul { margin: 4pt 0 8pt 0; padding-left: 22pt; }
li { margin-bottom: 3pt; }
strong { color: #1B5E20; }
em { font-style: italic; }
table {
  border-collapse: collapse;
  width: 100%;
  margin: 8pt 0 12pt 0;
  font-size: 9.5pt;
  page-break-inside: avoid;
}
th, td {
  border: 1px solid #bbb;
  padding: 6pt 8pt;
  text-align: left;
  vertical-align: top;
}
th { background: #E8F5E9; color: #1B5E20; font-weight: 600; }
hr { border: none; border-top: 1px solid #ccc; margin: 14pt 0; }
"""


def find_browser() -> Path:
    for p in BROWSER_CANDIDATES:
        if p.exists():
            return p
    for name in ("chrome", "msedge"):
        found = shutil.which(name)
        if found:
            return Path(found)
    raise SystemExit("ERROR: Chrome or Edge not found. Install one or adjust BROWSER_CANDIDATES.")


def strip_em_dashes(text: str) -> str:
    return text.replace("—", ", ").replace("&mdash;", ", ")


def md_to_html(md_path: Path, title: str) -> str:
    md = MarkdownIt("commonmark", {"html": False, "breaks": False, "linkify": True}).enable("table")
    source = strip_em_dashes(md_path.read_text(encoding="utf-8"))
    rendered = strip_em_dashes(md.render(source))
    title = strip_em_dashes(title)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>{CSS_RULES}</style>
</head>
<body>
{rendered}
</body>
</html>
"""


def html_to_pdf(browser: Path, html: str, dst: Path):
    dst = dst.resolve()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / "doc.html"
        html_path.write_text(html, encoding="utf-8")
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


def build():
    browser = find_browser()
    print(f"Using browser at: {browser}")
    for src, dst, title in SOURCES:
        if not src.exists():
            print(f"SKIP: {src} not found")
            continue
        html = md_to_html(src, title)
        html_to_pdf(browser, html, dst)
        print(f"OK: {src.name} -> {dst.name} ({dst.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
