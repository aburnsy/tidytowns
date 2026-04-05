# Site Restructure: Macros-Based Project Tracker - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace shell-script-generated static markdown with mkdocs-macros-plugin so that project/task pages are rendered automatically from simple frontmatter+prose files, and the Projects page groups projects by delivery year.

**Architecture:** A single Python hook file (`site/main.py`) uses `define_env()` to register macros and an `on_page_markdown` hook. The hook detects project pages and appends rendered metadata + task tables. Macros (`project_list_by_year()`, `my_tasks()`) are called from listing pages. All 43 project files are simplified to frontmatter + prose.

**Tech Stack:** MkDocs Material, mkdocs-macros-plugin, Python 3, PyYAML (bundled with mkdocs), uv

---

## File Structure

### Files to create
- `site/main.py` - mkdocs-macros hook module with `define_env()`, project/task scanning, rendering

### Files to modify
- `site/mkdocs.yml` - add `macros` plugin
- `site/docs/projects/index.md` - replace static placeholder with `{{ project_list_by_year() }}`
- `site/docs/index.md` - replace `<!-- PROJECT_LIST -->` block with `{{ project_list_by_year() }}`
- `site/docs/my-tasks.md` - replace static placeholder with `{{ my_tasks() }}`
- `scripts/new-project.sh` - update to produce simplified format (frontmatter + prose, add `delivery_year`)
- `scripts/new-task.sh` - update to produce simplified format (frontmatter + prose, `assignee` singular, `due` field)
- `CLAUDE.md` - update build commands, remove references to deleted scripts
- All 43 project `index.md` files - simplify to frontmatter + prose, add `delivery_year`

### Files to delete
- `scripts/generate-index.sh` - replaced by `project_list_by_year()` macro
- `scripts/generate-my-tasks.sh` - replaced by `my_tasks()` macro

---

## Task 1: Add mkdocs-macros-plugin to build and create skeleton hook

**Files:**
- Modify: `site/mkdocs.yml`
- Create: `site/main.py`

- [ ] **Step 1: Add macros plugin to mkdocs.yml**

In `site/mkdocs.yml`, add `macros` to the plugins list. It must come after `search` and before `tags`:

```yaml
plugins:
  - search
  - macros
  - tags
```

- [ ] **Step 2: Create site/main.py with skeleton define_env**

Create `site/main.py`:

```python
"""mkdocs-macros hook for TMB Tidy Towns project tracker.

Provides:
- on_page_markdown hook: auto-renders project metadata + task tables
- project_list_by_year() macro: grouped project listing for index pages
- my_tasks() macro: all open tasks grouped by assignee
"""

import os
import re
from pathlib import Path


def _read_frontmatter(filepath):
    """Read YAML frontmatter from a markdown file. Returns a dict."""
    text = Path(filepath).read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    fm_text = text[3:end].strip()
    body = text[end + 3:].strip()
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
        m = re.match(r'^(\w[\w_]*):\s*(.*)', line)
        if m:
            # Save previous list
            current_key = m.group(1)
            current_list = None
            val = m.group(2).strip().strip('"').strip("'")
            if val == "" or val == "[]":
                meta[current_key] = []
            elif val.startswith("[") and val.endswith("]"):
                # Inline list: [a, b, c]
                items = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
                meta[current_key] = items
                current_list = items
            else:
                meta[current_key] = val
    return meta, body


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
```

- [ ] **Step 3: Test that the site builds with the new plugin**

Run:
```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | head -30
```
Expected: Build succeeds with no errors. You should see "macros" listed among the plugins.

- [ ] **Step 4: Commit**

```bash
git add site/mkdocs.yml site/main.py
git commit -m "feat: add mkdocs-macros plugin with skeleton hook"
```

---

## Task 2: Implement _read_frontmatter and project scanning helpers

**Files:**
- Modify: `site/main.py`

- [ ] **Step 1: Verify _read_frontmatter works with an existing project file**

Run a quick test from the `site` directory:

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin python -c "
from main import _read_frontmatter
meta, body = _read_frontmatter('docs/projects/001-segregate-litter/index.md')
print('title:', meta.get('title'))
print('tags:', meta.get('tags'))
print('status:', meta.get('status'))
print('benefit:', meta.get('benefit'))
print('body starts:', body[:60])
"
```

Expected output:
```
title: Segregate collected litter into recyclables
tags: ['sustainability', 'tidiness']
status: Planned 2026
benefit: High
body starts: # Segregate collected litter into recyclables
```

If the output matches, the frontmatter parser works. If not, debug and fix `_read_frontmatter`.

- [ ] **Step 2: Add project scanning helper to main.py**

Add this function to `site/main.py`, above `define_env`:

```python
def _scan_projects(docs_dir):
    """Scan all project directories and return a list of project dicts."""
    projects_dir = Path(docs_dir) / "projects"
    projects = []
    for proj_dir in sorted(projects_dir.iterdir()):
        if not proj_dir.is_dir() or not re.match(r'^\d{3}-', proj_dir.name):
            continue
        index_file = proj_dir / "index.md"
        if not index_file.exists():
            continue
        meta, body = _read_frontmatter(str(index_file))
        # Parse delivery_year from frontmatter or from status field
        delivery_year = meta.get("delivery_year", "")
        if not delivery_year:
            status = meta.get("status", "")
            m = re.search(r'(\d{4})', status)
            delivery_year = m.group(1) if m else "Unscheduled"
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
```

- [ ] **Step 3: Verify project scanning works**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin python -c "
from main import _scan_projects
projects = _scan_projects('docs')
print(f'Found {len(projects)} projects')
for p in projects[:3]:
    print(f\"  {p['_folder']}: year={p['delivery_year']}, benefit={p.get('benefit')}\")
years = sorted(set(p['delivery_year'] for p in projects))
print('Years:', years)
"
```

Expected: `Found 43 projects`, years should be `['2026', '2027', '2028']`.

- [ ] **Step 4: Commit**

```bash
git add site/main.py
git commit -m "feat: add project and task scanning helpers"
```

---

## Task 3: Implement project_list_by_year() macro

**Files:**
- Modify: `site/main.py`
- Modify: `site/docs/projects/index.md`

- [ ] **Step 1: Replace the placeholder project_list_by_year in define_env**

In `site/main.py`, replace the `project_list_by_year` function inside `define_env` with:

```python
    @env.macro
    def project_list_by_year():
        """Render all projects grouped by delivery year."""
        docs_dir = env.conf["docs_dir"]
        projects = _scan_projects(docs_dir)

        # Group by year
        from collections import defaultdict
        by_year = defaultdict(list)
        for p in projects:
            by_year[p["delivery_year"]].append(p)

        # Sort benefit: High > Medium > Low
        benefit_order = {"High": 0, "Medium": 1, "Low": 2}

        # Current year first, then ascending
        import datetime
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
            sorted_projects = sorted(by_year[year], key=lambda p: benefit_order.get(p.get("benefit", "Low"), 9))
            for p in sorted_projects:
                title = p.get("title", p["_folder"])
                folder = p["_folder"]
                benefit = p.get("benefit", "")
                cost = p.get("cost_estimate", "")
                status = p.get("status", "")
                tags = ", ".join(p.get("tags", []))
                link = f"[{title}]({folder}/)"
                lines.append(f"| {link} | {benefit} | {cost} | {status} | {tags} |")
            lines.append("")
        return "\n".join(lines)
```

- [ ] **Step 2: Update projects/index.md to use the macro**

Replace the entire contents of `site/docs/projects/index.md` with:

```markdown
---
title: Projects
---

# Projects

Browse all Two Mile Borris Tidy Towns projects below, grouped by delivery year.

{{ project_list_by_year() }}
```

- [ ] **Step 3: Test the projects page renders**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -5
```

Then check the generated output:

```bash
cat site/projects/index.html | grep -o '<h2[^>]*>[^<]*</h2>' | head -5
```

Expected: `<h2>2026</h2>`, `<h2>2027</h2>`, `<h2>2028</h2>` headings present.

- [ ] **Step 4: Commit**

```bash
git add site/main.py site/docs/projects/index.md
git commit -m "feat: implement project_list_by_year macro and update projects page"
```

---

## Task 4: Update homepage to use macro

**Files:**
- Modify: `site/docs/index.md`

- [ ] **Step 1: Replace the PROJECT_LIST block on the homepage**

Replace the contents of `site/docs/index.md` with:

```markdown
---
title: Home
---

# TMB Tidy Towns - Community Projects

Welcome to the Two Mile Borris Tidy Towns project tracker. Here you'll find all the projects our community is working on to improve our village.

**Want to get involved?** [Propose a new project](propose-project.md) or [comment on an existing one](submit-idea.md).

**Volunteering?** Check [My Tasks](my-tasks.md) to see what's assigned to you.

---

{{ project_list_by_year() }}
```

- [ ] **Step 2: Build and verify the homepage**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -5
```

Then verify:

```bash
cat site/index.html | grep -o '<h2[^>]*>[^<]*</h2>' | head -5
```

Expected: Year headings present (`2026`, `2027`, `2028`).

- [ ] **Step 3: Commit**

```bash
git add site/docs/index.md
git commit -m "feat: update homepage to use project_list_by_year macro"
```

---

## Task 5: Implement on_page_markdown hook for project pages

**Files:**
- Modify: `site/main.py`

- [ ] **Step 1: Add the on_page_markdown hook inside define_env**

Add this at the end of the `define_env` function in `site/main.py`:

```python
    @env.event
    def on_page_markdown(markdown, page, **kwargs):
        """Auto-append metadata bar and task table to project pages."""
        # Only apply to project index pages
        src_path = page.file.src_path.replace("\\", "/")
        m = re.match(r'^projects/(\d{3}-[^/]+)/index\.md$', src_path)
        if not m:
            return markdown

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
                # Support legacy assignees list
                if not t_assignee:
                    assignees_list = t.get("assignees", [])
                    if isinstance(assignees_list, list):
                        t_assignee = ", ".join(assignees_list)
                    elif isinstance(assignees_list, str):
                        t_assignee = assignees_list
                t_due = t.get("due", "")
                t_status = t.get("status", "open")
                t_link = f"[{t_title}]({t['_filename']}/)"
                task_section += f"| {t_link} | {t_assignee} | {t_due} | {t_status} |\n"
        else:
            task_section += "*No tasks yet. Tasks will be added when the project is approved and assigned.*\n"

        # Navigation footer
        nav = "\n\n---\n\n[Comment on this project](../../submit-idea.md) | [Propose a new project](../../propose-project.md)\n"

        # Append everything after the existing markdown body
        suffix = f"\n\n{meta_bar}{tags_line}{inspired_line}{task_section}{nav}"
        return markdown + suffix
```

- [ ] **Step 2: Build and verify a project page**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -5
```

Then check a project page:

```bash
cat site/projects/001-segregate-litter/index.html | grep -oP '(Status|Cost|Benefit|Tasks)[^<]*' | head -10
```

Expected: `Status:`, `Cost:`, `Benefit:` metadata visible. `Tasks` section present.

- [ ] **Step 3: Commit**

```bash
git add site/main.py
git commit -m "feat: add on_page_markdown hook for auto-rendering project metadata and tasks"
```

---

## Task 6: Implement my_tasks() macro

**Files:**
- Modify: `site/main.py`
- Modify: `site/docs/my-tasks.md`

- [ ] **Step 1: Replace the placeholder my_tasks in define_env**

In `site/main.py`, replace the `my_tasks` function inside `define_env` with:

```python
    @env.macro
    def my_tasks():
        """Render all open tasks grouped by assignee."""
        docs_dir = env.conf["docs_dir"]
        projects = _scan_projects(docs_dir)

        from collections import defaultdict
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
```

- [ ] **Step 2: Update my-tasks.md to use the macro**

Replace the contents of `site/docs/my-tasks.md` with:

```markdown
---
title: My Tasks
---

# My Tasks

Find your tasks below, grouped by assignee. Use your browser's search (Ctrl+F) to find your name.

{{ my_tasks() }}
```

- [ ] **Step 3: Build and verify**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -5
```

Then verify (with no task files yet, should show "No open tasks"):

```bash
grep -o "No open tasks" site/my-tasks/index.html
```

Expected: `No open tasks`

- [ ] **Step 4: Commit**

```bash
git add site/main.py site/docs/my-tasks.md
git commit -m "feat: implement my_tasks macro and update my-tasks page"
```

---

## Task 7: Simplify all 43 project index.md files

**Files:**
- Modify: all `site/docs/projects/NNN-slug/index.md` files (43 files)

This task converts all project files from the current format (frontmatter + boilerplate headings/sections/links) to the new format (frontmatter with `delivery_year` + prose body only).

- [ ] **Step 1: Write a conversion script**

Create a temporary Python script `scripts/convert_projects.py`:

```python
"""One-time script to convert project files to new simplified format.

For each project index.md:
1. Read the existing frontmatter
2. Add delivery_year parsed from status field
3. Extract prose content (strip headings, task placeholders, nav links)
4. Write back as frontmatter + prose only
"""

import re
from pathlib import Path


def read_frontmatter_raw(filepath):
    """Read file, return (frontmatter_lines, body_text)."""
    text = Path(filepath).read_text(encoding="utf-8")
    if not text.startswith("---"):
        return [], text
    end_idx = text.index("---", 3)
    fm = text[3:end_idx].strip()
    body = text[end_idx + 3:].strip()
    return fm, body


def extract_delivery_year(fm_text):
    """Extract year from status field like 'Planned 2026'."""
    for line in fm_text.splitlines():
        if line.startswith("status:"):
            m = re.search(r'(\d{4})', line)
            if m:
                return m.group(1)
    return None


def clean_body(body):
    """Remove boilerplate headings and sections, keep meaningful prose."""
    lines = body.splitlines()
    output = []
    skip_section = False

    for line in lines:
        stripped = line.strip()

        # Skip the H1 title (redundant with frontmatter title)
        if stripped.startswith("# ") and not stripped.startswith("## "):
            continue

        # Skip boilerplate sections
        if stripped in ("## Tasks", "## Have your say"):
            skip_section = True
            continue

        # Real content headings end the skip
        if stripped.startswith("## ") and stripped not in ("## Tasks", "## Have your say"):
            skip_section = False
            # Convert ## headings to plain text emphasis since the hook handles structure
            # Actually keep them - they're part of the prose (e.g. "## What the adjudicator said")
            output.append(line)
            continue

        if skip_section:
            continue

        # Skip nav links
        if "[Comment on this project]" in stripped or "[Propose a new project]" in stripped:
            continue

        output.append(line)

    # Clean up leading/trailing blank lines
    text = "\n".join(output).strip()
    return text


def add_delivery_year_to_frontmatter(fm_text, year):
    """Insert delivery_year after title in frontmatter."""
    lines = fm_text.splitlines()
    new_lines = []
    added = False
    for line in lines:
        new_lines.append(line)
        if line.startswith("title:") and not added:
            new_lines.append(f"delivery_year: {year}")
            added = True
    if not added:
        new_lines.insert(0, f"delivery_year: {year}")
    return "\n".join(new_lines)


def convert_file(filepath):
    """Convert a single project file."""
    fm_text, body = read_frontmatter_raw(filepath)
    year = extract_delivery_year(fm_text)
    if year:
        fm_text = add_delivery_year_to_frontmatter(fm_text, year)
    cleaned = clean_body(body)
    new_content = f"---\n{fm_text}\n---\n\n{cleaned}\n"
    Path(filepath).write_text(new_content, encoding="utf-8")
    return year


if __name__ == "__main__":
    projects_dir = Path("site/docs/projects")
    for proj_dir in sorted(projects_dir.iterdir()):
        if not proj_dir.is_dir() or not re.match(r'^\d{3}-', proj_dir.name):
            continue
        index_file = proj_dir / "index.md"
        if not index_file.exists():
            continue
        year = convert_file(str(index_file))
        print(f"  Converted {proj_dir.name} (year={year})")
    print("Done.")
```

- [ ] **Step 2: Run the conversion script**

```bash
uv run python scripts/convert_projects.py
```

Expected: 43 lines of `Converted NNN-slug (year=YYYY)` output.

- [ ] **Step 3: Spot-check a few converted files**

Check the first project:

```bash
cat site/docs/projects/001-segregate-litter/index.md
```

Expected format:
```
---
title: "Segregate collected litter into recyclables"
delivery_year: 2026
tags:
  - sustainability
  - tidiness
status: "Planned 2026"
... (rest of frontmatter)
---

Currently all litter collected during cleanups goes to landfill. By separating recyclables during collection, we reduce waste and demonstrate environmental responsibility. Requires no budget - just a change in process.

## What the adjudicator said

The 2025 adjudicator noted that litter collected during cleanups is currently sent to landfill and recommended that we introduce a system to separate out recyclable materials at the point of collection.
```

No `# Title` heading, no `## Tasks`, no `## Have your say`, no nav links.

Check a project with no extra sections (e.g. 005):

```bash
cat site/docs/projects/005-mutt-mitt-dispenser/index.md
```

- [ ] **Step 4: Build the full site and verify**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -10
```

Expected: Clean build, no errors.

Check a rendered project page:

```bash
grep -c "Status:" site/projects/001-segregate-litter/index.html
```

Expected: At least 1 match (the metadata bar is being injected).

- [ ] **Step 5: Commit**

```bash
git add site/docs/projects/
git commit -m "refactor: simplify all 43 project files to frontmatter + prose format

Added delivery_year field. Removed boilerplate headings, task placeholders,
and navigation links (now auto-rendered by mkdocs-macros hook)."
```

- [ ] **Step 6: Delete the conversion script**

```bash
rm scripts/convert_projects.py
```

---

## Task 8: Delete old shell scripts and update CLAUDE.md

**Files:**
- Delete: `scripts/generate-index.sh`
- Delete: `scripts/generate-my-tasks.sh`
- Modify: `scripts/new-project.sh`
- Modify: `scripts/new-task.sh`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Delete the old generation scripts**

```bash
git rm scripts/generate-index.sh scripts/generate-my-tasks.sh
```

- [ ] **Step 2: Update new-project.sh to produce simplified format**

In `scripts/new-project.sh`, replace the `cat > "$project_dir/index.md"` heredoc (lines 184-208) with:

```bash
cat > "$project_dir/index.md" <<MDEOF
---
title: "$title"
delivery_year: $(echo "$status" | grep -oP '\d{4}' || echo "")
tags:
${tags_yaml}status: "$status"
owner: "$owner_val"
cost_estimate: "$cost_estimate"
benefit: "$benefit"
volunteer_hours: "$volunteer_hours"
${inspired_by_line}${special_award_line}---

${description:-*No description provided yet.*}
MDEOF
```

Key changes: added `delivery_year`, removed `# Title` heading, removed `## Description`, `## Tasks`, `## Have your say` sections and nav links.

- [ ] **Step 3: Update new-task.sh to use simplified field names**

In `scripts/new-task.sh`, replace the `cat > "$task_file"` heredoc (lines 186-200) with:

```bash
cat > "$task_file" <<MDEOF
---
title: "$task_title"
status: "$task_status"
assignee: ""
${due_date_line}${recurring_line}
${active_months_line}${tags_block}
---

${description:-*No description provided yet.*}
MDEOF
```

Key changes: changed `assignees` (list) to `assignee` (string), removed `# Title` heading and `## Description` section.

- [ ] **Step 4: Update CLAUDE.md**

In `CLAUDE.md`, make these changes:

Replace the build commands:
```
### Build & preview the site
```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs serve
```

### Build the site (production)
```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build
```
```

Remove the "Rebuild homepage project index" and "Rebuild volunteer task view" sections entirely (the `generate-index.sh` and `generate-my-tasks.sh` references).

Update the Architecture section - replace:
```
- `site/docs/projects/NNN-slug/task-*.md` - Task files within each project (assignees, due dates, status)
- `site/docs/projects/NNN-slug/task-*-template.md` - Recurring task templates
```

With:
```
- `site/docs/projects/NNN-slug/task-*.md` - Task files within each project (assignee, due date, status, evidence/photos)
- `site/main.py` - mkdocs-macros hook that auto-renders project metadata, task tables, and listing pages
```

Add to Key Conventions:
```
- **After modifying project/task files** - no need to run generation scripts; macros render everything at build time
```

And remove the old convention:
```
- **After modifying project/task files** - run `scripts/generate-index.sh` and `scripts/generate-my-tasks.sh` to update derived pages
```

- [ ] **Step 5: Commit**

```bash
git add scripts/new-project.sh scripts/new-task.sh CLAUDE.md
git commit -m "chore: delete old generation scripts, update CLI scripts and CLAUDE.md

Removed generate-index.sh and generate-my-tasks.sh (replaced by macros).
Updated new-project.sh and new-task.sh for simplified file format.
Updated CLAUDE.md with new build commands and conventions."
```

---

## Task 9: End-to-end verification

**Files:** None (verification only)

- [ ] **Step 1: Clean build**

```bash
cd site && rm -rf site/ && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1
```

Expected: Clean build with no errors or warnings.

- [ ] **Step 2: Verify Projects page has all 43 projects grouped by year**

```bash
grep -c '<tr>' site/projects/index.html
```

Expected: At least 43 rows (table rows for projects + header rows).

```bash
grep -oP '<h2[^>]*>[^<]*</h2>' site/projects/index.html
```

Expected: Headings for 2026, 2027, 2028.

- [ ] **Step 3: Verify a project page has auto-rendered metadata and tasks section**

```bash
grep "Status:" site/projects/001-segregate-litter/index.html | head -1
grep "Tasks" site/projects/001-segregate-litter/index.html | head -1
grep "Comment on this project" site/projects/001-segregate-litter/index.html | head -1
```

Expected: All three patterns found.

- [ ] **Step 4: Verify homepage has grouped project listing**

```bash
grep -oP '<h2[^>]*>[^<]*</h2>' site/index.html
```

Expected: Year headings present.

- [ ] **Step 5: Verify My Tasks page renders**

```bash
grep "No open tasks" site/my-tasks/index.html
```

Expected: Match found (no task files exist yet).

- [ ] **Step 6: Verify tags page works**

```bash
ls site/tags/index.html
```

Expected: File exists.

- [ ] **Step 7: Preview the site locally**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs serve
```

Manually check in browser:
- Homepage shows grouped projects
- Projects page shows grouped projects
- Individual project page shows metadata bar + tasks section
- Tags page lists all tags
- My Tasks page shows "No open tasks"

- [ ] **Step 8: Final commit if any fixes were needed**

```bash
git add -A
git status
# Only commit if there are changes
git commit -m "fix: end-to-end verification fixes"
```
