# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the project management and strategy platform for Two Mile Borris (TMB) Tidy Towns, Co. Tipperary. It consists of:

1. **A MkDocs Material website** (`site/`) deployed to GitHub Pages - public project tracker for the committee
2. **Private application strategy files** (`private/`) - never published
3. **Research data** (`research/`) - competition analysis, adjudication reports, score tracking
4. **CLI scripts** (`scripts/`) for managing content

## Commands

### Build & preview the site
```bash
cd site && uv run --with mkdocs-material mkdocs serve
```

### Build the site (production)
```bash
cd site && uv run --with mkdocs-material mkdocs build
```

### Add a new project (interactive)
```bash
bash scripts/new-project.sh
```

### Add a new task to a project (interactive)
```bash
bash scripts/new-task.sh
```

### Generate recurring tasks for next 3 months
```bash
bash scripts/generate-recurring.sh
```

### Rebuild homepage project index
```bash
bash scripts/generate-index.sh
```

### Rebuild volunteer task view
```bash
bash scripts/generate-my-tasks.sh
```

### Run research scripts
```bash
uv run --with pymupdf python research/extract_scores.py
```

## Architecture

- `site/docs/projects/NNN-slug/index.md` - Project pages with frontmatter (status, owner, cost, benefit, tags)
- `site/docs/projects/NNN-slug/task-*.md` - Task files within each project (assignees, due dates, status)
- `site/docs/projects/NNN-slug/task-*-template.md` - Recurring task templates
- `private/` - Application strategy, marks analysis, adjudicator tracker. NEVER publish these.
- `research/` - Results booklets, reports, analysis scripts. Not published.

## Key Conventions

- **Use `uv` for Python** - not pip or raw python. Example: `uv run --with package python script.py`
- **Public site language** - never mention marks, points, or scoring on the public site. Use "benefit: High/Medium/Low" instead.
- **Volunteer names** - shortnames only (first name + last initial). No PII.
- **Biodiversity projects** - follow pollinators.ie All-Ireland Pollinator Plan guidelines (no-mow first, native seed only)
- **After modifying project/task files** - run `scripts/generate-index.sh` and `scripts/generate-my-tasks.sh` to update derived pages
- **Marks analysis stays private** - `private/marks-analysis.md` maps projects to estimated marks. The public site only shows benefit level.

## Competition Context

- TMB is Category B (201-1000 population), Tipperary North
- 2025 score: 318/550. Target: 380+ (county winner) in 3 years, 390+ (medal) in 5 years
- From 2026, total marks increase to 600 (Nature & Biodiv and Sustainability go from 55 to 80 each)
- Weakest categories: Sustainability (31%), Streetscape (51%), Nature & Biodiversity (53%)
