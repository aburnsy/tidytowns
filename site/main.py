"""mkdocs-macros hook for TMB Tidy Towns project tracker.

Provides:
- on_page_markdown hook: auto-renders project metadata bar
- project_list_by_year() macro: grouped project listing for index pages
"""

import datetime
import re
from collections import defaultdict
from pathlib import Path


def _read_frontmatter(filepath):
    """Read YAML frontmatter from a markdown file. Returns (dict, body_str)."""
    text = Path(filepath).read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    fm_text = text[3:end].strip()
    body = text[end + 3 :].strip()
    meta = {}
    current_key = None
    current_list = None
    for line in fm_text.splitlines():
        # List item
        if line.startswith("  - ") and current_key:
            if current_list is None:
                current_list = []
            val = line[4:].strip().strip('"').strip("'")
            current_list.append(val)
            meta[current_key] = current_list
            continue
        # Key-value
        m = re.match(r"^(\w[\w_]*):\s*(.*)", line)
        if m:
            current_key = m.group(1)
            current_list = None
            val = m.group(2).strip().strip('"').strip("'")
            if val == "" or val == "[]":
                meta[current_key] = []
            elif val.startswith("[") and val.endswith("]"):
                items = [
                    v.strip().strip('"').strip("'")
                    for v in val[1:-1].split(",")
                    if v.strip()
                ]
                meta[current_key] = items
                current_list = items
            else:
                meta[current_key] = val
    return meta, body


def _scan_projects(docs_dir):
    """Scan all project directories and return a list of project dicts."""
    projects_dir = Path(docs_dir) / "projects"
    projects = []
    for proj_dir in sorted(projects_dir.iterdir()):
        if not proj_dir.is_dir() or not re.match(r"^\d{3}-", proj_dir.name):
            continue
        index_file = proj_dir / "index.md"
        if not index_file.exists():
            continue
        meta, body = _read_frontmatter(str(index_file))
        # Parse delivery_year from frontmatter or from status field
        delivery_year = meta.get("delivery_year", "")
        if not delivery_year:
            status = meta.get("status", "")
            year_match = re.search(r"(\d{4})", status)
            delivery_year = year_match.group(1) if year_match else "Unscheduled"
        meta["delivery_year"] = str(delivery_year)
        meta["_folder"] = proj_dir.name
        meta["_body"] = body
        meta["_dir"] = str(proj_dir)
        projects.append(meta)
    return projects


def define_env(env):
    """Hook called by mkdocs-macros-plugin."""

    @env.macro
    def project_list_by_year():
        """Render all projects grouped by delivery year."""
        docs_dir = env.conf["docs_dir"]
        projects = _scan_projects(docs_dir)

        # Determine link prefix based on calling page location
        src_path = env.page.file.src_path.replace("\\", "/")
        if src_path.startswith("projects/"):
            prefix = ""
        else:
            prefix = "projects/"

        by_year = defaultdict(list)
        for p in projects:
            by_year[p["delivery_year"]].append(p)

        benefit_order = {"High": 0, "Medium": 1, "Low": 2}
        current_year = str(datetime.date.today().year)
        years = sorted(by_year.keys())
        if current_year in years:
            years.remove(current_year)
            years.insert(0, current_year)

        lines = []
        for year in years:
            lines.append(f"## {year}\n")
            lines.append("| Project | Benefit | Cost | Status |")
            lines.append("|---------|---------|------|--------|")
            sorted_projects = sorted(
                by_year[year],
                key=lambda p: benefit_order.get(p.get("benefit", "Low"), 9),
            )
            for p in sorted_projects:
                title = p.get("title", p["_folder"])
                folder = p["_folder"]
                benefit = p.get("benefit", "")
                cost = p.get("cost_estimate", "")
                status = p.get("status", "")
                link = f"[{title}]({prefix}{folder}/index.md)"
                lines.append(f"| {link} | {benefit} | {cost} | {status} |")
            lines.append("")
        return "\n".join(lines)

    pass  # Macros registered above; page hook is on_post_page_macros() below


def on_post_page_macros(env):
    """Auto-append metadata bar to project pages.

    Called by mkdocs-macros after macro rendering for each page.
    Modifies env.markdown in place for project index pages.
    """
    page = env.page
    src_path = page.file.src_path.replace("\\", "/")
    m = re.match(r"^projects/(\d{3}-[^/]+)/index\.md$", src_path)
    if not m:
        return

    meta = page.meta

    # Build metadata bar
    parts = []
    status = meta.get("status", "")
    if status:
        parts.append(f"**Status:** {status}")
    cost = meta.get("cost_estimate", "")
    if cost:
        parts.append(f"**Cost:** {cost}")
    benefit = meta.get("benefit", "")
    if benefit:
        parts.append(f"**Benefit:** {benefit}")
    award = meta.get("special_award", "")
    if award:
        parts.append(f"**Award:** {award}")

    meta_bar = " | ".join(parts)

    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    tags_block = ""
    if tags:
        chips = []
        for t in tags:
            slug = str(t).strip().lower().replace("_", "-")
            label = slug.replace("-", " ").title()
            chips.append(
                f'<span class="project-tag tag-{slug}">{label}</span>'
            )
        tags_block = (
            '\n\n<div class="project-tags" markdown="0">'
            + "".join(chips)
            + "</div>"
        )

    inspired = meta.get("inspired_by", "")
    inspired_line = ""
    if inspired:
        inspired_line = f"\n\n*Inspired by: {inspired}*"

    # Navigation footer
    nav = "\n\n---\n\n*Questions or feedback? [Email us](mailto:info@tmbvillage.ie) at info@tmbvillage.ie.*\n"

    suffix = f"\n\n{meta_bar}{tags_block}{inspired_line}{nav}"
    env.markdown += suffix
