"""mkdocs-macros hook for TMB Tidy Towns project tracker.

Provides:
- on_post_page_macros hook: auto-renders project metadata bar
- project_list_by_year() macro: grouped active project listing
- completed_project_list() macro: grouped completed project listing
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


def _scan_dir(docs_dir, subdir):
    """Scan a project subdirectory and return a list of project dicts."""
    base = Path(docs_dir) / subdir
    projects = []
    if not base.exists():
        return projects
    for proj_dir in sorted(base.iterdir()):
        if not proj_dir.is_dir() or not re.match(r"^\d{3}-", proj_dir.name):
            continue
        index_file = proj_dir / "index.md"
        if not index_file.exists():
            continue
        meta, body = _read_frontmatter(str(index_file))
        delivery_year = meta.get("delivery_year", "")
        if not delivery_year:
            status = meta.get("status", "")
            year_match = re.search(r"(\d{4})", status)
            delivery_year = year_match.group(1) if year_match else "Unscheduled"
        meta["delivery_year"] = str(delivery_year)
        meta["_folder"] = proj_dir.name
        meta["_body"] = body
        meta["_dir"] = str(proj_dir)
        meta["_subdir"] = subdir
        projects.append(meta)
    return projects


def _render_table(projects, prefix):
    """Render a sorted-by-benefit project table for a single year/section."""
    benefit_order = {"High": 0, "Medium": 1, "Low": 2}
    sorted_projects = sorted(
        projects,
        key=lambda p: benefit_order.get(p.get("benefit", "Low"), 9),
    )
    lines = ["| Project | Benefit | Cost | Status |", "|---------|---------|------|--------|"]
    for p in sorted_projects:
        title = p.get("title", p["_folder"])
        folder = p["_folder"]
        benefit = p.get("benefit", "")
        cost = p.get("cost_estimate", "")
        status = p.get("status", "")
        link = f"[{title}]({prefix}{folder}/index.md)"
        lines.append(f"| {link} | {benefit} | {cost} | {status} |")
    return lines


def define_env(env):
    """Hook called by mkdocs-macros-plugin."""

    @env.macro
    def project_list_by_year():
        """Render active projects (in projects/) grouped by delivery year."""
        docs_dir = env.conf["docs_dir"]
        projects = _scan_dir(docs_dir, "projects")

        src_path = env.page.file.src_path.replace("\\", "/")
        prefix = "" if src_path.startswith("projects/") else "projects/"

        by_year = defaultdict(list)
        for p in projects:
            by_year[p["delivery_year"]].append(p)

        current_year = str(datetime.date.today().year)
        years = sorted(by_year.keys())
        if current_year in years:
            years.remove(current_year)
            years.insert(0, current_year)

        lines = []
        for year in years:
            lines.append(f"## {year}\n")
            lines.extend(_render_table(by_year[year], prefix))
            lines.append("")
        return "\n".join(lines)

    @env.macro
    def future_project_list():
        """Render long-horizon / aspirational projects (in future/) grouped by delivery year."""
        docs_dir = env.conf["docs_dir"]
        projects = _scan_dir(docs_dir, "future")

        src_path = env.page.file.src_path.replace("\\", "/")
        prefix = "" if src_path.startswith("future/") else "future/"

        if not projects:
            return "*No future projects logged yet.*"

        by_year = defaultdict(list)
        for p in projects:
            by_year[p["delivery_year"]].append(p)

        years = sorted(by_year.keys())

        lines = []
        for year in years:
            heading = year if year != "Unscheduled" else "Long-term / unscheduled"
            lines.append(f"## {heading}\n")
            lines.extend(_render_table(by_year[year], prefix))
            lines.append("")
        return "\n".join(lines)

    @env.macro
    def completed_project_list():
        """Render completed projects (in completed/) grouped by completion year."""
        docs_dir = env.conf["docs_dir"]
        projects = _scan_dir(docs_dir, "completed")

        src_path = env.page.file.src_path.replace("\\", "/")
        prefix = "" if src_path.startswith("completed/") else "completed/"

        if not projects:
            return "*No completed projects logged yet.*"

        by_year = defaultdict(list)
        for p in projects:
            year = p.get("completed_year") or p.get("delivery_year") or "Completed"
            by_year[str(year)].append(p)

        # Most-recent completion first
        years = sorted(by_year.keys(), reverse=True)

        lines = []
        for year in years:
            lines.append(f"## {year}\n")
            lines.extend(_render_table(by_year[year], prefix))
            lines.append("")
        return "\n".join(lines)


def on_post_page_macros(env):
    """Auto-append metadata bar to project pages (active or completed)."""
    page = env.page
    src_path = page.file.src_path.replace("\\", "/")
    m = re.match(r"^(projects|completed|future)/(\d{3}-[^/]+)/index\.md$", src_path)
    if not m:
        return

    meta = page.meta

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

    nav = "\n\n---\n\n*Questions or feedback? [Email us](mailto:info@tmbvillage.ie) at info@tmbvillage.ie.*\n"

    suffix = f"\n\n{meta_bar}{tags_block}{inspired_line}{nav}"
    env.markdown += suffix
