# Site Restructure: Macros-Based Project Tracker

**Date:** 2026-04-05
**Status:** Approved

## Problem

1. Project markdown files contain repeated boilerplate (headings, links, metadata display) across 40+ files
2. The Projects page (`projects/index.md`) is empty - the shell script `generate-index.sh` only updates the homepage
3. No task files exist despite the convention being defined
4. The homepage project list is a flat bullet list with no year grouping
5. Tags exist in frontmatter but aren't used for filtering/grouping on the projects page

## Solution

Replace shell-script-generated static markdown with `mkdocs-macros-plugin`. A Python hook (`site/main.py`) reads frontmatter and task files at build time, injecting rendered HTML/markdown into pages automatically.

## Architecture

### Build setup

- Add `mkdocs-macros-plugin` as a dependency alongside `mkdocs-material`
- Build command becomes: `uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs serve`
- Add `macros` to the `plugins` list in `mkdocs.yml`
- Create `site/main.py` - auto-discovered by mkdocs-macros as the hook module

### main.py hook

The `define_env(env)` function registers hooks and macros:

- **`on_page_markdown` hook**: Intercepts page rendering. For project pages (path matches `projects/NNN-slug/index.md`), it appends:
  - Metadata bar (status badge, cost, benefit, tags, award, owner)
  - Task summary table (auto-discovered from `task-*.md` files in the same directory)
  - Navigation links (comment, propose)
- **`project_list_by_year()` macro**: Called by `projects/index.md`. Scans all project directories, reads frontmatter, groups by `delivery_year`, sorts current year first then ascending. Renders a table per year section.
- **`my_tasks()` macro**: Called by `my-tasks.md`. Scans all task files across all projects, groups by assignee, renders per-person task lists.

### Project file format

Each project is `site/docs/projects/NNN-slug/index.md`:

```yaml
---
title: Segregate collected litter into recyclables
delivery_year: 2026
status: planned
cost_estimate: "€0"
benefit: High
tags: [sustainability, tidiness]
owner: ""
special_award: Sustainability & Circular Economy
inspired_by: 2025 adjudication recommendation
---

Currently all litter collected during cleanups goes to landfill.
By separating recyclables during collection, we reduce waste.
```

Key changes from current format:
- `delivery_year` added as an integer for sorting/grouping
- `status` simplified to lowercase values: `planned`, `in-progress`, `done`, `wont-do`
- Body is prose only - no headings, no sections, no links. The hook injects everything else.

### Task file format

Separate files inside the project folder: `task-NNN-slug.md`

```yaml
---
title: Buy colour-coded recycling bags
assignee: Mary K
due: 2026-06
status: open
---

Description of work, evidence, photos.

![Bags purchased](bags-photo.jpg)
```

Task statuses: `open`, `in-progress`, `done`

Tasks are auto-discovered by the project page hook. Each task gets its own page (for photos/evidence) and appears as a row in the project's task summary table.

### Projects page (`projects/index.md`)

```markdown
---
title: Projects
---

{{ project_list_by_year() }}
```

Renders as year-grouped tables:

```
## 2026

| Project | Benefit | Cost | Status | Tags |
|---------|---------|------|--------|------|
| [Segregate litter](001-segregate-litter/) | High | €0 | Planned | sustainability |

## 2027
...

## 2028
...
```

Within each year, projects are sorted by benefit: High > Medium > Low.

### Homepage (`index.md`)

Keep the current welcome text and links. Replace the `<!-- PROJECT_LIST -->` markers with the same `{{ project_list_by_year() }}` macro used on the projects page, so both pages show the year-grouped project tables.

### My Tasks page (`my-tasks.md`)

```markdown
---
title: My Tasks
---

{{ my_tasks() }}
```

Scans all task files, groups by assignee, shows project context.

### Tags

The existing `tags` plugin in mkdocs.yml already supports the `tags:` frontmatter field. The `/tags/` page auto-generates. No additional work needed beyond ensuring all projects have tags.

## Files to create

- `site/main.py` - macros hook with `define_env()`, project/task scanning, rendering functions

## Files to modify

- `site/mkdocs.yml` - add `macros` plugin
- `site/docs/projects/index.md` - replace static content with `{{ project_list_by_year() }}`
- `site/docs/index.md` - replace `<!-- PROJECT_LIST -->` markers with macro call
- `site/docs/my-tasks.md` - replace static content with `{{ my_tasks() }}`
- All 43 project `index.md` files - simplify to frontmatter + prose, add `delivery_year`

## Files to delete

- `scripts/generate-index.sh` - replaced by macros
- `scripts/generate-my-tasks.sh` - replaced by macros

## CLAUDE.md updates

- Update build commands to include `--with mkdocs-macros-plugin`
- Remove references to generate-index.sh and generate-my-tasks.sh
- Document the new project/task file format

## Out of scope

- Task creation CLI scripts (can be added later)
- Filtering/search on the projects page (MkDocs Material search handles this)
- Progress page changes
