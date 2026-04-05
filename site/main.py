"""mkdocs-macros hook for TMB Tidy Towns project tracker.

Provides:
- on_page_markdown hook: auto-renders project metadata + task tables
- project_list_by_year() macro: grouped project listing for index pages
- my_tasks() macro: all open tasks grouped by assignee
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


def _scan_tasks(project_dir):
    """Scan task-*.md files in a project directory. Returns list of task dicts."""
    tasks = []
    proj_path = Path(project_dir)
    for task_file in sorted(proj_path.glob("task-*.md")):
        if task_file.name.endswith("-template.md"):
            continue
        meta, body = _read_frontmatter(str(task_file))
        meta["_filename"] = task_file.stem
        meta["_body"] = body
        tasks.append(meta)
    return tasks


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
            lines.append("| Project | Benefit | Cost | Status | Tags |")
            lines.append("|---------|---------|------|--------|------|")
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
                tags = ", ".join(p.get("tags", []))
                link = f"[{title}]({prefix}{folder}/index.md)"
                lines.append(f"| {link} | {benefit} | {cost} | {status} | {tags} |")
            lines.append("")
        return "\n".join(lines)

    @env.macro
    def my_tasks():
        """Render all open tasks grouped by assignee."""
        docs_dir = env.conf["docs_dir"]
        projects = _scan_projects(docs_dir)

        by_assignee = defaultdict(list)
        for p in projects:
            tasks = _scan_tasks(p["_dir"])
            for t in tasks:
                status = t.get("status", "open")
                if status == "done":
                    continue
                assignee = t.get("assignee", "")
                if not assignee:
                    assignees_list = t.get("assignees", [])
                    if isinstance(assignees_list, list) and assignees_list:
                        for a in assignees_list:
                            by_assignee[a].append((p, t))
                        continue
                    elif isinstance(assignees_list, str) and assignees_list:
                        assignee = assignees_list
                    else:
                        assignee = "Unassigned"
                by_assignee[assignee].append((p, t))

        if not by_assignee:
            return "*No open tasks found.*\n"

        lines = []
        for assignee in sorted(by_assignee.keys()):
            lines.append(f"## {assignee}\n")
            lines.append("| Task | Project | Due | Status |")
            lines.append("|------|---------|-----|--------|")
            for p, t in by_assignee[assignee]:
                t_title = t.get("title", t["_filename"])
                p_title = p.get("title", p["_folder"])
                folder = p["_folder"]
                t_file = t["_filename"]
                t_due = t.get("due", "")
                t_status = t.get("status", "open")
                t_link = f"[{t_title}](projects/{folder}/{t_file}/)"
                p_link = f"[{p_title}](projects/{folder}/)"
                lines.append(f"| {t_link} | {p_link} | {t_due} | {t_status} |")
            lines.append("")
        return "\n".join(lines)

    pass  # Macros registered above; page hook is on_post_page_macros() below


def on_post_page_macros(env):
    """Auto-append metadata bar and task table to project pages.

    Called by mkdocs-macros after macro rendering for each page.
    Modifies env.markdown in place for project index pages.
    """
    page = env.page
    src_path = page.file.src_path.replace("\\", "/")
    m = re.match(r"^projects/(\d{3}-[^/]+)/index\.md$", src_path)
    if not m:
        return

    meta = page.meta
    folder = m.group(1)
    docs_dir = env.conf["docs_dir"]
    project_dir = Path(docs_dir) / "projects" / folder

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
    owner = meta.get("owner", "")
    if owner:
        parts.append(f"**Owner:** {owner}")
    award = meta.get("special_award", "")
    if award:
        parts.append(f"**Award:** {award}")

    meta_bar = " | ".join(parts)

    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    tags_line = ""
    if tags:
        tags_line = f"\n\n**Tags:** {', '.join(tags)}"

    inspired = meta.get("inspired_by", "")
    inspired_line = ""
    if inspired:
        inspired_line = f"\n\n*Inspired by: {inspired}*"

    # Build task table
    tasks = _scan_tasks(str(project_dir))
    task_section = "\n\n---\n\n## Tasks\n\n"
    if tasks:
        task_section += "| Task | Assignee | Due | Status |\n"
        task_section += "|------|----------|-----|--------|\n"
        for t in tasks:
            t_title = t.get("title", t["_filename"])
            t_assignee = t.get("assignee", "")
            if not t_assignee:
                assignees_list = t.get("assignees", [])
                if isinstance(assignees_list, list):
                    t_assignee = ", ".join(assignees_list)
                elif isinstance(assignees_list, str):
                    t_assignee = assignees_list
            t_due = t.get("due", "")
            t_status = t.get("status", "open")
            t_link = f"[{t_title}]({t['_filename']}/)"
            task_section += (
                f"| {t_link} | {t_assignee} | {t_due} | {t_status} |\n"
            )
    else:
        task_section += "*No tasks yet. Tasks will be added when the project is approved and assigned.*\n"

    # Navigation footer
    nav = "\n\n---\n\n[Comment on this project](../../submit-idea.md) | [Propose a new project](../../propose-project.md)\n"

    suffix = f"\n\n{meta_bar}{tags_line}{inspired_line}{task_section}{nav}"
    env.markdown += suffix
