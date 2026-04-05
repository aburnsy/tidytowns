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
        return "_project_list_by_year placeholder_"

    @env.macro
    def my_tasks():
        """Render all open tasks grouped by assignee."""
        return "_my_tasks placeholder_"
