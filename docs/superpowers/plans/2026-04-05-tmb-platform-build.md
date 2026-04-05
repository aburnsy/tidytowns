# TMB Tidy Towns Platform - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GitHub Pages website for TMB Tidy Towns that serves as a project management platform for the committee, with CLI tools for adding projects/tasks, and private application strategy files.

**Architecture:** MkDocs Material static site deployed via GitHub Actions. Projects are folders containing an index.md + task markdown files. Three bash CLI scripts handle content creation (new-project, new-task, generate-recurring). A build script regenerates the homepage index and volunteer task view from frontmatter metadata. Private application strategy files live outside the published site directory.

**Tech Stack:** MkDocs Material (Python/pip via uv), GitHub Pages, GitHub Actions, Bash scripts, Google Forms (external)

**Spec:** `docs/superpowers/specs/2026-04-05-tmb-tidy-towns-strategy-design.md`

---

### Task 1: Initialize Git Repository

**Files:**
- Create: `.gitignore`
- Create: `.gitattributes`

- [ ] **Step 1: Initialize git**

```bash
git init
```

- [ ] **Step 2: Create .gitignore**

```
# MkDocs build output
site/site/

# Python
__pycache__/
*.pyc
.venv/

# Superpowers brainstorm sessions
.superpowers/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
```

- [ ] **Step 3: Create .gitattributes for PDF handling**

```
*.pdf filter=lfs diff=lfs merge=lfs -text
*.docx filter=lfs diff=lfs merge=lfs -text
```

Note: If git-lfs is not installed, skip this step and just commit PDFs directly. They're ~15MB each which is fine for a small repo.

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: initialize repository"
```

---

### Task 2: MkDocs Material Setup

**Files:**
- Create: `site/mkdocs.yml`
- Create: `site/docs/stylesheets/extra.css`

- [ ] **Step 1: Verify uv is available**

```bash
uv --version
```
Expected: version string like `uv 0.10.2`

- [ ] **Step 2: Create mkdocs.yml**

Create `site/mkdocs.yml`:

```yaml
site_name: TMB Tidy Towns
site_description: Two Mile Borris Tidy Towns - Community Projects
site_url: ""

theme:
  name: material
  palette:
    primary: green
    accent: light green
  features:
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.suggest
    - search.highlight
    - content.tabs.link
    - navigation.indexes
  icon:
    logo: material/leaf

plugins:
  - search
  - tags:
      tags_file: tags.md

extra_css:
  - stylesheets/extra.css

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - attr_list
  - md_in_html
  - tables
  - toc:
      permalink: true
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg

nav:
  - Home: index.md
  - Projects: projects/
  - My Tasks: my-tasks.md
  - Progress: progress.md
  - Propose a Project: propose-project.md
  - Comment on a Project: submit-idea.md
  - Tags: tags.md
  - About: about.md
```

- [ ] **Step 3: Create extra.css for status badges and project cards**

Create `site/docs/stylesheets/extra.css`:

```css
/* Status badges */
.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.8em;
  font-weight: 600;
  color: white;
}
.status-planned { background-color: #1976d2; }
.status-will-do { background-color: #388e3c; }
.status-wont-do { background-color: #757575; }
.status-discussion { background-color: #f57c00; }
.status-pending { background-color: #90a4ae; }
.status-in-progress { background-color: #1976d2; }
.status-done { background-color: #388e3c; }

/* Benefit badges */
.benefit-high { color: #388e3c; font-weight: bold; }
.benefit-medium { color: #f57c00; font-weight: bold; }
.benefit-low { color: #757575; }

/* Project cards on homepage */
.project-card {
  border: 1px solid var(--md-default-fg-color--lightest);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}
.project-card:hover {
  border-color: var(--md-accent-fg-color);
}
.project-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  font-size: 0.85em;
  color: var(--md-default-fg-color--light);
  margin-top: 8px;
}
```

- [ ] **Step 4: Create tags index page**

Create `site/docs/tags.md`:

```markdown
---
title: Browse by Category
---

# Browse by Category

Find projects by their Tidy Towns category.

[TAGS]
```

- [ ] **Step 5: Verify MkDocs builds**

```bash
cd site && uv run --with mkdocs-material mkdocs build 2>&1 | tail -5
```
Expected: Build succeeds (will warn about missing pages, that's fine)

- [ ] **Step 6: Commit**

```bash
git add site/mkdocs.yml site/docs/stylesheets/extra.css site/docs/tags.md
git commit -m "feat: add MkDocs Material site configuration"
```

---

### Task 3: Core Site Pages

**Files:**
- Create: `site/docs/index.md`
- Create: `site/docs/about.md`
- Create: `site/docs/progress.md`
- Create: `site/docs/submit-idea.md`
- Create: `site/docs/propose-project.md`
- Create: `site/docs/my-tasks.md`

- [ ] **Step 1: Create homepage (index.md)**

Create `site/docs/index.md`:

```markdown
---
title: Home
---

# TMB Tidy Towns - Community Projects

Welcome to the Two Mile Borris Tidy Towns project tracker. Here you'll find all the projects our community is working on to improve our village.

**Want to get involved?** [Propose a new project](propose-project.md) or [comment on an existing one](submit-idea.md).

**Volunteering?** Check [My Tasks](my-tasks.md) to see what's assigned to you.

---

<!-- This section is auto-generated by scripts/generate-index.sh -->
<!-- PROJECT_LIST_START -->
*No projects yet. Run `scripts/generate-index.sh` to populate.*
<!-- PROJECT_LIST_END -->
```

- [ ] **Step 2: Create about page**

Create `site/docs/about.md`:

```markdown
---
title: About
---

# About TMB Tidy Towns

Two Mile Borris (Buirios Leith) is situated in the northeast of County Tipperary, approximately 7km east of Thurles and easily accessible from the M8.

Our Tidy Towns committee of 27 members, supported by volunteers, works year-round to make Two Mile Borris a better place to live, work and visit.

## Our Committees

The community of Two Mile Borris is actively involved through several groups:

- **Development Group & Tidy Towns** - creating a vibrant village
- **Parents Association** - supporting school activities
- **Christmas Lights Committee** - bringing festive cheer
- **Graveyard Committee** - maintaining and extending the graveyard
- **Defibrillator Group** - emergency medical response

## Get Involved

- **Join us**: Contact info@tmbvillage.ie
- **Fundraising**: Support our [Split the Pot](https://www.tmbvillage.ie/) weekly draw
- **Ideas**: [Propose a project](propose-project.md) or [comment on existing ones](submit-idea.md)

## Links

- [TMB Village Website](https://www.tmbvillage.ie/)
- [SuperValu TidyTowns](https://www.tidytowns.ie/)
- [All-Ireland Pollinator Plan](https://pollinators.ie/)
```

- [ ] **Step 3: Create progress page**

Create `site/docs/progress.md`:

```markdown
---
title: Progress
---

# Our Progress

## Where We Are

Two Mile Borris entered the TidyTowns competition in 2013-2019 and again from 2024. Here's our journey:

| Year | Score | Change |
|------|-------|--------|
| 2024 | 307   | -      |
| 2025 | 318   | +11    |

## Our Goals

We're working towards making Two Mile Borris the best it can be across all areas of village life:

- **Environmental sustainability** - reducing waste, conserving water, promoting renewable energy
- **Nature and biodiversity** - protecting and enhancing our local wildlife and habitats
- **Community spaces** - maintaining and improving our streetscape, green areas, and public spaces
- **Community engagement** - involving all residents in village improvement

## How Our Projects Help

Each project on this site contributes to one or more aspects of village improvement. Projects are rated by their expected benefit:

- **High benefit** - significant positive impact on village life
- **Medium benefit** - meaningful improvement in a specific area
- **Low benefit** - small but worthwhile enhancement

## Tipperary North Context

We're part of a strong tradition of community effort across Tipperary North, with many villages working hard to improve their areas.
```

- [ ] **Step 4: Create submit-idea page**

Create `site/docs/submit-idea.md`:

```markdown
---
title: Comment on a Project
---

# Share Your Ideas

Have thoughts on one of our projects? We'd love to hear from you!

Use the form below to share ideas, suggest improvements, or volunteer for a specific project.

<!-- REPLACE_WITH_GOOGLE_FORM_EMBED -->

!!! info "Google Form Setup Required"
    To set up the comment form:

    1. Create a Google Form with fields: Your name (optional), Which project? (dropdown), Your idea/comment, Location in village (optional)
    2. Get the embed URL from Google Forms (Send > Embed)
    3. Replace this notice with: `<iframe src="YOUR_FORM_URL" width="100%" height="800" frameborder="0">Loading...</iframe>`

Your responses are reviewed by our committee and help shape our village improvement work.
```

- [ ] **Step 5: Create propose-project page**

Create `site/docs/propose-project.md`:

```markdown
---
title: Propose a Project
---

# Propose a New Project

Have an idea for improving Two Mile Borris? We want to hear it!

Whether it's a biodiversity initiative, a streetscape improvement, or a community event - all ideas are welcome.

<!-- REPLACE_WITH_GOOGLE_FORM_EMBED -->

!!! info "Google Form Setup Required"
    To set up the proposal form:

    1. Create a Google Form with fields: Your name (optional), Project idea, Category (dropdown: Community / Streetscape / Green Spaces / Nature & Biodiversity / Sustainability / Tidiness / Residential / Approach Roads), Why is it important?, Estimated cost (optional), Location (optional)
    2. Get the embed URL from Google Forms (Send > Embed)
    3. Replace this notice with: `<iframe src="YOUR_FORM_URL" width="100%" height="800" frameborder="0">Loading...</iframe>`

All proposals are reviewed by the committee at our regular meetings.
```

- [ ] **Step 6: Create my-tasks page (placeholder)**

Create `site/docs/my-tasks.md`:

```markdown
---
title: My Tasks
---

# My Tasks

Use the search box above to find tasks assigned to you (search your name).

<!-- This section is auto-generated by scripts/generate-my-tasks.sh -->
<!-- TASKS_START -->
*No tasks yet. Run `scripts/generate-my-tasks.sh` to populate.*
<!-- TASKS_END -->
```

- [ ] **Step 7: Verify build**

```bash
cd site && uv run --with mkdocs-material mkdocs build 2>&1 | tail -5
```
Expected: Clean build

- [ ] **Step 8: Commit**

```bash
git add site/docs/
git commit -m "feat: add core site pages (home, about, progress, forms, tasks)"
```

---

### Task 4: Project Template and First 5 Example Projects

**Files:**
- Create: `site/docs/projects/001-segregate-litter/index.md`
- Create: `site/docs/projects/002-composting/index.md`
- Create: `site/docs/projects/003-feature-bog-walk/index.md`
- Create: `site/docs/projects/009-unmown-verge-strips/index.md`
- Create: `site/docs/projects/028-bog-walk-nature-trail/index.md`

These 5 represent a mix: zero-cost quick win (#1), low-cost (#2), application-only (#3), biodiversity best practice (#9), and long-term showcase (#28).

- [ ] **Step 1: Create project 001 - Segregate collected litter**

Create `site/docs/projects/001-segregate-litter/index.md`:

```markdown
---
title: "Segregate collected litter into recyclables"
tags:
  - sustainability
  - tidiness
status: "Planned 2026"
owner: ""
cost_estimate: "€0"
benefit: "High"
volunteer_hours: "2hrs initial setup, then 15 min per cleanup"
inspired_by: "2025 adjudication recommendation"
special_award: "Sustainability & Circular Economy"
---

# Segregate Collected Litter

## Description

Currently, all litter collected during cleanups goes into one pile and to landfill. By separating recyclables during collection, we reduce waste and demonstrate environmental responsibility.

This requires no budget - just a change in process. Bring separate bags for recyclables and general waste on each litter pick.

## What the adjudicator said

> The 2025 adjudicator noted that collected litter currently goes to landfill and recommended recycling the litter collected as a sustainable action.

## How to implement

1. Source colour-coded bags (or use different bin bags) for each cleanup
2. Brief volunteers at the start of each litter pick on what goes where
3. Arrange recycling drop-off for sorted materials
4. Document the process with photos for the application

## Tasks

*Tasks will be added when the project is approved and assigned.*

## Have your say

[Comment on this project](../../submit-idea.md) | [Propose a new project](../../propose-project.md)
```

- [ ] **Step 2: Create project 002 - Composting**

Create `site/docs/projects/002-composting/index.md`:

```markdown
---
title: "Start composting organic waste for reuse in beds"
tags:
  - sustainability
status: "Planned 2026"
owner: ""
cost_estimate: "€50-80"
benefit: "High"
volunteer_hours: "3hrs setup, then 30 min/month maintenance"
inspired_by: "2025 adjudication recommendation"
special_award: "Sustainability & Circular Economy"
---

# Community Composting

## Description

Set up a composting station for organic waste collected during village maintenance. The compost can be reused in our flower beds and planters, closing the loop on green waste.

## What the adjudicator said

> The 2025 adjudicator recommended investigating composting organic waste as it can be reused in gardens and beds.

## How to implement

1. Source a compost bin (or build from salvaged timber - consistent with our existing approach)
2. Identify a suitable, discreet location
3. Establish a rota for turning and maintaining the compost
4. Use finished compost in village beds and planters
5. Photograph and document for the application

## Tasks

*Tasks will be added when the project is approved and assigned.*

## Have your say

[Comment on this project](../../submit-idea.md) | [Propose a new project](../../propose-project.md)
```

- [ ] **Step 3: Create project 003 - Feature bog walk in application**

Create `site/docs/projects/003-feature-bog-walk/index.md`:

```markdown
---
title: "Feature the Bog Walk Loop in our application"
tags:
  - community
  - nature-biodiversity
  - green-spaces
status: "Planned 2026"
owner: ""
cost_estimate: "€0"
benefit: "High"
volunteer_hours: "4hrs (writing, photography)"
inspired_by: "Research analysis - bog walk not mentioned in 2025 application"
---

# Feature the Bog Walk Loop

## Description

The Bog Walk Loop is one of Two Mile Borris's biggest amenity assets, yet it was not mentioned at all in our 2025 TidyTowns application. This project ensures it is prominently featured in our next application with photographs, description, and details of improvement works.

The bog walk touches multiple assessment areas: green spaces, nature and biodiversity, community amenity, and approach roads (as a walking route). Featuring it properly could improve our assessment across several categories.

## How to implement

1. Photograph the bog walk in all seasons (link to seasonal photography project)
2. Document the restoration work being carried out
3. Describe the biodiversity value of the bog habitat
4. Include on the application map with clear legend reference
5. Reference in multiple categories of the application form

## Tasks

*Tasks will be added when the project is approved and assigned.*

## Have your say

[Comment on this project](../../submit-idea.md) | [Propose a new project](../../propose-project.md)
```

- [ ] **Step 4: Create project 009 - Unmown verge strips**

Create `site/docs/projects/009-unmown-verge-strips/index.md`:

```markdown
---
title: "Leave unmown strips on approach road verges for wildlife"
tags:
  - nature-biodiversity
  - approach-roads
status: "Planned 2026"
owner: ""
cost_estimate: "€0-30 (signage)"
benefit: "Medium"
volunteer_hours: "Less than current (reduces mowing!)"
inspired_by: "2025 adjudication recommendation"
references:
  - title: "All-Ireland Pollinator Plan - Managing Grassland"
    url: "https://pollinators.ie/grasslands/"
---

# Unmown Verge Strips for Wildlife

## Description

Preserve unmown strips along the inside section of approach road verges where traffic safety permits. This allows native wildflowers to emerge from the existing seed bank and supports pollinators, following All-Ireland Pollinator Plan guidelines.

This project actually **saves money** - less mowing means less fuel and volunteer time.

## What the adjudicator said

> The 2025 adjudicator recommended preserving an unmown strip of inside section unmown and managed for nature on approach verges where traffic safety permits.

## Best practice (pollinators.ie)

Following the All-Ireland Pollinator Plan:

- **Don't sow commercial wildflower mixes** - let the natural seed bank in the soil emerge
- **Reduce mowing frequency** - allow wildflowers to flower and set seed
- **Remove dock leaves and thistles monthly** (Apr-Sep) - these are the main weeds to manage
- **Install small "managed for wildlife" signs** - so unmown areas don't look neglected
- Only consider sowing native Yellow Rattle if grasses are too dominant (suppresses grass, lets wildflowers compete)

## Tasks

*Tasks will be added when the project is approved and assigned.*

## Have your say

[Comment on this project](../../submit-idea.md) | [Propose a new project](../../propose-project.md)
```

- [ ] **Step 5: Create project 028 - Bog walk nature trail transformation**

Create `site/docs/projects/028-bog-walk-nature-trail/index.md`:

```markdown
---
title: "Transform the Bog Walk into a Biodiversity Nature Trail"
tags:
  - nature-biodiversity
  - green-spaces
  - community
status: "Planned 2027"
owner: ""
cost_estimate: "€1,000-3,000 (on top of existing restoration budget)"
benefit: "High"
volunteer_hours: "Significant - phased over 12+ months"
inspired_by: "Silvermines Nature Trail (scored 51/55 in Nature & Biodiversity)"
special_award: "Leave No Trace"
references:
  - title: "All-Ireland Pollinator Plan"
    url: "https://pollinators.ie/"
  - title: "Leave No Trace Ireland"
    url: "https://www.leavenotraceireland.org/"
---

# Bog Walk Nature Trail

## Description

Transform the existing Bog Walk Loop from a walking path into a biodiversity nature trail with multiple habitat zones, interpretation panels, species identification boards, and an open-air learning area.

This is inspired by Silvermines village, whose Nature Trail is the centrepiece of their biodiversity work and helped them score 51/55 (93%) in Nature & Biodiversity - compared to TMB's 29/55 (53%). Their trail includes meadows, wetland areas, a riverside section, an open classroom, and extensive information signage.

The bog walk already has the natural habitats - it just needs interpretation and presentation to unlock its full potential.

## Phased approach

**Phase 1 (2026)**: Restore path surface (already funded). Feature in application. Begin wildlife surveys to document species.

**Phase 2 (2027)**: Install 3-4 interpretation panels identifying key habitats (bog, hedgerow, grassland). Add species ID boards. Create a simple open-air seating/classroom area for school visits.

**Phase 3 (2028)**: Develop additional habitat features (bird boxes, bug hotels along route). Link to heritage trail. Seek Leave No Trace accreditation.

## Best practice

- Follow pollinators.ie guidelines for habitat management
- Engage Tipperary County Council Biodiversity Officer for survey support
- Consult with local school (Green Schools program) for educational elements
- Document all species found for biodiversity records and application

## Tasks

*Tasks will be added when the project is approved and assigned.*

## Have your say

[Comment on this project](../../submit-idea.md) | [Propose a new project](../../propose-project.md)
```

- [ ] **Step 6: Verify build**

```bash
cd site && uv run --with mkdocs-material mkdocs build 2>&1 | tail -5
```
Expected: Clean build with project pages

- [ ] **Step 7: Commit**

```bash
git add site/docs/projects/
git commit -m "feat: add first 5 project pages as templates"
```

---

### Task 5: CLI Script - new-project.sh

**Files:**
- Create: `scripts/new-project.sh`

- [ ] **Step 1: Create new-project.sh**

Create `scripts/new-project.sh`:

```bash
#!/bin/bash
# Interactive script to create a new TidyTowns project
set -e

PROJECTS_DIR="site/docs/projects"

echo "=== Create New TMB Tidy Towns Project ==="
echo ""

# 1. Project number
EXISTING=$(ls -d "$PROJECTS_DIR"/[0-9]* 2>/dev/null | wc -l)
NEXT_NUM=$(printf "%03d" $((EXISTING + 1)))
echo "Next project number: $NEXT_NUM"

# 2. Title
read -p "Project title: " TITLE
if [ -z "$TITLE" ]; then echo "Title is required."; exit 1; fi

# 3. Slug
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//' | cut -c1-50)
FOLDER="${NEXT_NUM}-${SLUG}"
echo "Folder: $PROJECTS_DIR/$FOLDER"

# 4. Category tags
echo ""
echo "Category tags (enter numbers, comma-separated):"
echo "  1) community"
echo "  2) streetscape"
echo "  3) green-spaces"
echo "  4) nature-biodiversity"
echo "  5) sustainability"
echo "  6) tidiness"
echo "  7) residential"
echo "  8) approach-roads"
read -p "Tags [e.g. 1,4,5]: " TAG_INPUT

TAGS=""
IFS=',' read -ra TAG_NUMS <<< "$TAG_INPUT"
TAG_NAMES=("" "community" "streetscape" "green-spaces" "nature-biodiversity" "sustainability" "tidiness" "residential" "approach-roads")
for num in "${TAG_NUMS[@]}"; do
  num=$(echo "$num" | tr -d ' ')
  if [ -n "${TAG_NAMES[$num]}" ]; then
    TAGS="${TAGS}  - ${TAG_NAMES[$num]}\n"
  fi
done

# 5. Status
echo ""
echo "Status:"
echo "  1) Planned 2026"
echo "  2) Planned 2027"
echo "  3) Planned 2028"
echo "  4) Will Do"
echo "  5) Under Discussion"
read -p "Status [1-5]: " STATUS_NUM
STATUS_OPTIONS=("" "Planned 2026" "Planned 2027" "Planned 2028" "Will Do" "Under Discussion")
STATUS="${STATUS_OPTIONS[$STATUS_NUM]:-Under Discussion}"

# 6. Owner
read -p "Owner (shortname, or leave blank): " OWNER

# 7. Cost estimate
read -p "Cost estimate [e.g. €0, €50-100]: " COST

# 8. Benefit
echo ""
echo "Benefit level:"
echo "  1) High"
echo "  2) Medium"
echo "  3) Low"
read -p "Benefit [1-3]: " BENEFIT_NUM
BENEFIT_OPTIONS=("" "High" "Medium" "Low")
BENEFIT="${BENEFIT_OPTIONS[$BENEFIT_NUM]:-Medium}"

# 9. Volunteer hours
read -p "Volunteer hours estimate: " VOL_HOURS

# 10. Inspired by
read -p "Inspired by (or leave blank): " INSPIRED

# 11. Special award
echo ""
echo "Special award (optional):"
echo "  1) Endeavour Award"
echo "  2) Sustainability & Circular Economy"
echo "  3) Leave No Trace"
echo "  4) Inclusion Award"
echo "  5) Active Travel"
echo "  6) Tiny TidyTowns"
echo "  0) None"
read -p "Special award [0-6]: " AWARD_NUM
AWARD_OPTIONS=("" "Endeavour Award" "Sustainability & Circular Economy" "Leave No Trace" "Inclusion Award" "Active Travel" "Tiny TidyTowns")
SPECIAL_AWARD="${AWARD_OPTIONS[$AWARD_NUM]:-}"

# 12. Description
echo ""
echo "Description (press Enter twice to finish):"
DESCRIPTION=""
while IFS= read -r line; do
  [ -z "$line" ] && break
  DESCRIPTION="${DESCRIPTION}${line}\n"
done

# Create the project
mkdir -p "$PROJECTS_DIR/$FOLDER"

cat > "$PROJECTS_DIR/$FOLDER/index.md" << ENDOFFILE
---
title: "$TITLE"
tags:
$(echo -e "$TAGS")status: "$STATUS"
owner: "$OWNER"
cost_estimate: "$COST"
benefit: "$BENEFIT"
volunteer_hours: "$VOL_HOURS"
inspired_by: "$INSPIRED"
special_award: "$SPECIAL_AWARD"
---

# $TITLE

## Description

$(echo -e "$DESCRIPTION")

## Tasks

*Tasks will be added when the project is approved and assigned.*

## Have your say

[Comment on this project](../../submit-idea.md) | [Propose a new project](../../propose-project.md)
ENDOFFILE

echo ""
echo "Created: $PROJECTS_DIR/$FOLDER/index.md"
echo "Next: add tasks with scripts/new-task.sh"
```

- [ ] **Step 2: Make executable and test**

```bash
chmod +x scripts/new-project.sh
```

Manually test by running `bash scripts/new-project.sh` and following the prompts.

- [ ] **Step 3: Commit**

```bash
git add scripts/new-project.sh
git commit -m "feat: add interactive new-project CLI script"
```

---

### Task 6: CLI Script - new-task.sh

**Files:**
- Create: `scripts/new-task.sh`

- [ ] **Step 1: Create new-task.sh**

Create `scripts/new-task.sh`:

```bash
#!/bin/bash
# Interactive script to create a new task within a project
set -e

PROJECTS_DIR="site/docs/projects"

echo "=== Create New Task ==="
echo ""

# 1. Select project
echo "Available projects:"
PROJECTS=($(ls -d "$PROJECTS_DIR"/[0-9]* 2>/dev/null))
if [ ${#PROJECTS[@]} -eq 0 ]; then
  echo "No projects found. Create a project first with scripts/new-project.sh"
  exit 1
fi

for i in "${!PROJECTS[@]}"; do
  NAME=$(basename "${PROJECTS[$i]}")
  # Extract title from frontmatter
  PTITLE=$(grep '^title:' "${PROJECTS[$i]}/index.md" 2>/dev/null | head -1 | sed 's/title: *"*//;s/"*$//')
  echo "  $((i+1))) $NAME - $PTITLE"
done

read -p "Select project [1-${#PROJECTS[@]}]: " PROJ_NUM
PROJ_IDX=$((PROJ_NUM - 1))
PROJECT_PATH="${PROJECTS[$PROJ_IDX]}"
echo "Project: $(basename "$PROJECT_PATH")"

# 2. Task title
echo ""
read -p "Task title: " TASK_TITLE
if [ -z "$TASK_TITLE" ]; then echo "Title is required."; exit 1; fi

# 3. Task slug
TASK_SLUG=$(echo "$TASK_TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//' | cut -c1-50)
TASK_FILE="task-${TASK_SLUG}.md"

# 4. One-off or recurring?
echo ""
echo "Task type:"
echo "  1) One-off"
echo "  2) Recurring"
read -p "Type [1-2]: " TASK_TYPE

RECURRING_YAML=""
if [ "$TASK_TYPE" = "2" ]; then
  echo ""
  echo "Frequency:"
  echo "  1) Weekly"
  echo "  2) Bi-monthly"
  echo "  3) Monthly"
  echo "  4) Seasonal (twice a year)"
  read -p "Frequency [1-4]: " FREQ_NUM
  FREQ_OPTIONS=("" "weekly" "bi-monthly" "monthly" "seasonal")
  FREQUENCY="${FREQ_OPTIONS[$FREQ_NUM]:-monthly}"

  read -p "Active months [e.g. Apr-Sep, or Year-round]: " ACTIVE_MONTHS
  RECURRING_YAML="recurring: \"$FREQUENCY\"\nactive_months: \"$ACTIVE_MONTHS\""
  TASK_FILE="task-${TASK_SLUG}-template.md"
  STATUS="template"
else
  STATUS="pending"
fi

# 5. Assignees
echo ""
read -p "Assignees (comma-separated shortnames, or blank): " ASSIGNEES_INPUT
ASSIGNEES=""
if [ -n "$ASSIGNEES_INPUT" ]; then
  IFS=',' read -ra NAMES <<< "$ASSIGNEES_INPUT"
  for name in "${NAMES[@]}"; do
    name=$(echo "$name" | sed 's/^ *//;s/ *$//')
    ASSIGNEES="${ASSIGNEES}  - \"${name}\"\n"
  done
fi

# 6. Due date (for one-off)
DUE_DATE=""
if [ "$TASK_TYPE" = "1" ]; then
  read -p "Due date [YYYY-MM-DD, or blank]: " DUE_DATE
fi

# 7. Description
echo ""
echo "Task description (press Enter twice to finish):"
TASK_DESC=""
while IFS= read -r line; do
  [ -z "$line" ] && break
  TASK_DESC="${TASK_DESC}${line}\n"
done

# 8. Tags (inherit from project)
PROJ_TAGS=$(sed -n '/^tags:/,/^[^ ]/p' "$PROJECT_PATH/index.md" | grep '^ *-' | head -5)

# Build the file
cat > "$PROJECT_PATH/$TASK_FILE" << ENDOFFILE
---
title: "$TASK_TITLE"
status: "$STATUS"
$(if [ -n "$ASSIGNEES" ]; then echo "assignees:"; echo -e "$ASSIGNEES"; fi)
$(if [ -n "$DUE_DATE" ]; then echo "due_date: \"$DUE_DATE\""; fi)
$(if [ -n "$RECURRING_YAML" ]; then echo -e "$RECURRING_YAML"; fi)
$PROJ_TAGS
---

$(echo -e "$TASK_DESC")
ENDOFFILE

echo ""
echo "Created: $PROJECT_PATH/$TASK_FILE"
if [ "$TASK_TYPE" = "2" ]; then
  echo "This is a recurring task template. Run scripts/generate-recurring.sh to create dated instances."
fi
```

- [ ] **Step 2: Make executable**

```bash
chmod +x scripts/new-task.sh
```

- [ ] **Step 3: Commit**

```bash
git add scripts/new-task.sh
git commit -m "feat: add interactive new-task CLI script"
```

---

### Task 7: CLI Script - generate-recurring.sh

**Files:**
- Create: `scripts/generate-recurring.sh`

- [ ] **Step 1: Create generate-recurring.sh**

Create `scripts/generate-recurring.sh`:

```bash
#!/bin/bash
# Generate dated task files from recurring task templates for the next 3 months
set -e

PROJECTS_DIR="site/docs/projects"
MONTHS_AHEAD=${1:-3}

echo "=== Generating Recurring Tasks ($MONTHS_AHEAD months ahead) ==="

# Get current date parts
CURRENT_YEAR=$(date +%Y)
CURRENT_MONTH=$(date +%-m)

# Month name mapping
MONTH_NAMES=("" "Jan" "Feb" "Mar" "Apr" "May" "Jun" "Jul" "Aug" "Sep" "Oct" "Nov" "Dec")

# Parse active_months like "Apr-Sep" into month numbers
parse_active_months() {
  local range="$1"
  if [ "$range" = "Year-round" ] || [ -z "$range" ]; then
    echo "1 2 3 4 5 6 7 8 9 10 11 12"
    return
  fi

  local start_name=$(echo "$range" | cut -d'-' -f1)
  local end_name=$(echo "$range" | cut -d'-' -f2)
  local start_num=1 end_num=12

  for i in $(seq 1 12); do
    if [ "${MONTH_NAMES[$i]}" = "$start_name" ]; then start_num=$i; fi
    if [ "${MONTH_NAMES[$i]}" = "$end_name" ]; then end_num=$i; fi
  done

  seq $start_num $end_num
}

GENERATED=0

# Find all recurring task templates
find "$PROJECTS_DIR" -name "task-*-template.md" | while read template; do
  PROJECT_DIR=$(dirname "$template")
  TEMPLATE_BASE=$(basename "$template" | sed 's/-template\.md$//')

  # Extract recurring info
  FREQUENCY=$(grep '^recurring:' "$template" | sed 's/recurring: *"*//;s/"*$//')
  ACTIVE=$(grep '^active_months:' "$template" | sed 's/active_months: *"*//;s/"*$//')
  TITLE=$(grep '^title:' "$template" | sed 's/title: *"*//;s/"*$//')

  if [ -z "$FREQUENCY" ]; then continue; fi

  ACTIVE_MONTHS=$(parse_active_months "$ACTIVE")

  # Determine which months to generate
  for offset in $(seq 0 $((MONTHS_AHEAD - 1))); do
    TARGET_MONTH=$(( (CURRENT_MONTH + offset - 1) % 12 + 1 ))
    TARGET_YEAR=$CURRENT_YEAR
    if [ $((CURRENT_MONTH + offset)) -gt 12 ]; then
      TARGET_YEAR=$((CURRENT_YEAR + 1))
    fi

    # Check if month is active
    IS_ACTIVE=false
    for m in $ACTIVE_MONTHS; do
      if [ "$m" = "$TARGET_MONTH" ]; then IS_ACTIVE=true; break; fi
    done
    if [ "$IS_ACTIVE" = false ]; then continue; fi

    # Skip bi-monthly on odd offsets
    if [ "$FREQUENCY" = "bi-monthly" ] && [ $((offset % 2)) -ne 0 ]; then continue; fi

    # Generate filename
    MONTH_PAD=$(printf "%02d" $TARGET_MONTH)
    LAST_DAY=$(date -d "$TARGET_YEAR-$MONTH_PAD-01 +1 month -1 day" +%d 2>/dev/null || echo "28")
    DATED_FILE="$PROJECT_DIR/${TEMPLATE_BASE}-${TARGET_YEAR}-${MONTH_PAD}.md"

    # Skip if already exists
    if [ -f "$DATED_FILE" ]; then continue; fi

    # Copy template, update status and add due_date
    sed "s/status: \"template\"/status: \"pending\"/" "$template" | \
    sed "/^---$/,/^---$/{ /^status:/a due_date: \"${TARGET_YEAR}-${MONTH_PAD}-${LAST_DAY}\"
    }" > "$DATED_FILE"

    echo "  Created: $DATED_FILE"
    GENERATED=$((GENERATED + 1))
  done
done

echo ""
echo "Done. Generated $GENERATED task files."
```

- [ ] **Step 2: Make executable**

```bash
chmod +x scripts/generate-recurring.sh
```

- [ ] **Step 3: Commit**

```bash
git add scripts/generate-recurring.sh
git commit -m "feat: add recurring task generation script"
```

---

### Task 8: Build Scripts - generate-index.sh and generate-my-tasks.sh

**Files:**
- Create: `scripts/generate-index.sh`
- Create: `scripts/generate-my-tasks.sh`

- [ ] **Step 1: Create generate-index.sh**

This scans all project folders and rebuilds the homepage project list.

Create `scripts/generate-index.sh`:

```bash
#!/bin/bash
# Regenerate the homepage project listing from project frontmatter
set -e

PROJECTS_DIR="site/docs/projects"
INDEX_FILE="site/docs/index.md"

echo "=== Generating Project Index ==="

# Build project list markdown
PROJECT_LIST=""
WONTDO_LIST=""

for project_dir in $(ls -d "$PROJECTS_DIR"/[0-9]* 2>/dev/null | sort); do
  INDEX="$project_dir/index.md"
  if [ ! -f "$INDEX" ]; then continue; fi

  FOLDER=$(basename "$project_dir")
  TITLE=$(grep '^title:' "$INDEX" | head -1 | sed 's/title: *"*//;s/"*$//')
  STATUS=$(grep '^status:' "$INDEX" | head -1 | sed 's/status: *"*//;s/"*$//')
  COST=$(grep '^cost_estimate:' "$INDEX" | head -1 | sed 's/cost_estimate: *"*//;s/"*$//')
  BENEFIT=$(grep '^benefit:' "$INDEX" | head -1 | sed 's/benefit: *"*//;s/"*$//')
  OWNER=$(grep '^owner:' "$INDEX" | head -1 | sed 's/owner: *"*//;s/"*$//')
  AWARD=$(grep '^special_award:' "$INDEX" | head -1 | sed 's/special_award: *"*//;s/"*$//')

  # Count tasks
  TASK_COUNT=$(find "$project_dir" -name "task-*.md" -not -name "*template*" 2>/dev/null | wc -l)
  DONE_COUNT=$(grep -l 'status: "done"' "$project_dir"/task-*.md 2>/dev/null | wc -l)

  OWNER_STR=""
  if [ -n "$OWNER" ]; then OWNER_STR=" | Owner: **$OWNER**"; fi
  AWARD_STR=""
  if [ -n "$AWARD" ]; then AWARD_STR=" | :trophy: $AWARD"; fi
  TASKS_STR=""
  if [ "$TASK_COUNT" -gt 0 ]; then TASKS_STR=" | Tasks: $DONE_COUNT/$TASK_COUNT done"; fi

  ENTRY="- [**$TITLE**](projects/$FOLDER/) — $STATUS | Cost: $COST | Benefit: **$BENEFIT**${OWNER_STR}${AWARD_STR}${TASKS_STR}"

  if [ "$STATUS" = "Won't Do" ]; then
    WONTDO_LIST="${WONTDO_LIST}\n${ENTRY}"
  else
    PROJECT_LIST="${PROJECT_LIST}\n${ENTRY}"
  fi
done

# Replace the project list section in index.md
HEADER=$(sed '/<!-- PROJECT_LIST_START -->/q' "$INDEX_FILE")
FOOTER=$(sed -n '/<!-- PROJECT_LIST_END -->/,$p' "$INDEX_FILE")

cat > "$INDEX_FILE" << ENDOFFILE
${HEADER}

$(echo -e "$PROJECT_LIST")

$(if [ -n "$WONTDO_LIST" ]; then
echo ""
echo "<details><summary>Archived / Won't Do projects</summary>"
echo ""
echo -e "$WONTDO_LIST"
echo ""
echo "</details>"
fi)

${FOOTER}
ENDOFFILE

echo "Updated: $INDEX_FILE"
echo "Projects listed: $(echo -e "$PROJECT_LIST" | grep -c '\S') active"
```

- [ ] **Step 2: Create generate-my-tasks.sh**

Create `scripts/generate-my-tasks.sh`:

```bash
#!/bin/bash
# Regenerate the My Tasks page from all task files
set -e

PROJECTS_DIR="site/docs/projects"
TASKS_FILE="site/docs/my-tasks.md"

echo "=== Generating My Tasks Page ==="

# Collect all tasks
TASKS_MD=""
TASK_COUNT=0

for project_dir in $(ls -d "$PROJECTS_DIR"/[0-9]* 2>/dev/null | sort); do
  PROJECT_FOLDER=$(basename "$project_dir")
  PROJECT_TITLE=$(grep '^title:' "$project_dir/index.md" 2>/dev/null | head -1 | sed 's/title: *"*//;s/"*$//')

  for task_file in $(find "$project_dir" -name "task-*.md" -not -name "*template*" 2>/dev/null | sort); do
    TASK_TITLE=$(grep '^title:' "$task_file" | head -1 | sed 's/title: *"*//;s/"*$//')
    TASK_STATUS=$(grep '^status:' "$task_file" | head -1 | sed 's/status: *"*//;s/"*$//')
    DUE=$(grep '^due_date:' "$task_file" | head -1 | sed 's/due_date: *"*//;s/"*$//')
    ASSIGNEES=$(sed -n '/^assignees:/,/^[^ ]/p' "$task_file" | grep '^ *-' | sed 's/^ *- *"*//;s/"*$//' | tr '\n' ', ' | sed 's/, $//')

    if [ "$TASK_STATUS" = "done" ]; then continue; fi
    if [ -z "$TASK_TITLE" ]; then continue; fi

    DUE_STR=""
    if [ -n "$DUE" ]; then DUE_STR=" | Due: $DUE"; fi
    ASSIGN_STR=""
    if [ -n "$ASSIGNEES" ]; then ASSIGN_STR=" | Assigned: **$ASSIGNEES**"; fi

    TASKS_MD="${TASKS_MD}\n| $TASK_TITLE | [$PROJECT_TITLE](projects/$PROJECT_FOLDER/) | $TASK_STATUS | ${DUE:-—} | ${ASSIGNEES:-Unassigned} |"
    TASK_COUNT=$((TASK_COUNT + 1))
  done
done

# Build the page
HEADER=$(sed '/<!-- TASKS_START -->/q' "$TASKS_FILE")
FOOTER=$(sed -n '/<!-- TASKS_END -->/,$p' "$TASKS_FILE")

cat > "$TASKS_FILE" << ENDOFFILE
${HEADER}

| Task | Project | Status | Due Date | Assigned To |
|------|---------|--------|----------|-------------|
$(echo -e "$TASKS_MD")

${FOOTER}
ENDOFFILE

echo "Updated: $TASKS_FILE"
echo "Open tasks listed: $TASK_COUNT"
```

- [ ] **Step 3: Make executable**

```bash
chmod +x scripts/generate-index.sh scripts/generate-my-tasks.sh
```

- [ ] **Step 4: Run both generators and verify**

```bash
bash scripts/generate-index.sh
bash scripts/generate-my-tasks.sh
cd site && uv run --with mkdocs-material mkdocs build 2>&1 | tail -5
```

Expected: Both scripts run, site builds cleanly

- [ ] **Step 5: Commit**

```bash
git add scripts/generate-index.sh scripts/generate-my-tasks.sh site/docs/index.md site/docs/my-tasks.md
git commit -m "feat: add index and my-tasks build scripts"
```

---

### Task 9: GitHub Actions Deploy Pipeline

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: Create deploy workflow**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy MkDocs to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'site/**'
      - '.github/workflows/deploy.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install MkDocs Material
        run: pip install mkdocs-material

      - name: Build site
        run: cd site && mkdocs build --strict

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site/site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: add GitHub Actions deploy pipeline for MkDocs"
```

---

### Task 10: Private Application Strategy Files

**Files:**
- Create: `private/application-guide.md`
- Create: `private/adjudicator-tracker.md`
- Create: `private/photo-checklist.md`
- Create: `private/3-5-year-plan.md`
- Create: `private/marks-analysis.md`

- [ ] **Step 1: Create marks analysis (private scoring data)**

Create `private/marks-analysis.md`:

```markdown
# TMB Marks Analysis (PRIVATE - DO NOT PUBLISH)

## Current Scores (2025)

| Category | Max | 2024 | 2025 | % | Target 2026 |
|---|---|---|---|---|---|
| Community | 80 | 43 | 45 | 56% | 52 |
| Streetscape | 80 | 39 | 41 | 51% | 48 |
| Green Spaces | 80 | 42 | 43 | 54% | 50 |
| Nature & Biodiv | 55 | 28 | 29 | 53% | 38 |
| Sustainability | 55 | 16 | 17 | 31% | 28 |
| Tidiness | 90 | 62 | 64 | 71% | 70 |
| Residential | 55 | 37 | 38 | 69% | 42 |
| Approach Roads | 55 | 40 | 41 | 75% | 43 |
| **TOTAL** | **550** | **307** | **318** | **58%** | **~371** |

## Benchmarks

| Village | Score | Category |
|---|---|---|
| Rosscarbery (Tidiest Village) | 399 | B |
| Emly (Regional Winner) | 395 | B |
| Silvermines (Tipp North leader) | 383 | B |
| **Two Mile Borris** | **318** | **B** |

## Medal Thresholds (based on 2025 winner scoring 400)

- Gold: 390+ (Cat A&B within 10)
- Silver: 385+ (within 15)
- Bronze: 380+ (within 20)
- Endeavour: Biggest % improvement in county

## Project-to-Marks Mapping

| # | Project | Marks Est | Cost | Marks/€ |
|---|---------|-----------|------|---------|
| 1 | Segregate litter | +3-5 | €0 | Infinite |
| 2 | Composting | +3-4 | €50-80 | 50 |
| 3 | Feature bog walk | +5-8 | €0 | Infinite |
| 6 | Better application | +5-10 | €0 | Infinite |
| 28 | Bog walk nature trail | +8-15 | €1-3k | 5 |
| ... | ... | ... | ... | ... |

*Complete marks mapping maintained here. Public site shows benefit: High/Medium/Low only.*
```

- [ ] **Step 2: Create adjudicator tracker**

Create `private/adjudicator-tracker.md`:

```markdown
# Adjudicator Recommendations Tracker (PRIVATE)

## 2025 Recommendations

| # | Category | Recommendation | Status | Project # | Action Taken |
|---|----------|---------------|--------|-----------|-------------|
| 1 | Streetscape | Paint derelict property openings + window boxes | Not started | 014 | Need owner cooperation |
| 2 | Streetscape | Replica window in forge - contact Heritage Officer | Not started | 022 | TODO: Contact Heritage Officer |
| 3 | Streetscape | Repaint bollards at monument | Not started | 013 | |
| 4 | Green Spaces | Use All-Ireland Pollinator Plan species (repeated from 2024) | Not started | 012 | |
| 5 | Green Spaces | Wildflower bed at church grounds | Not started | 011 | |
| 6 | Green Spaces | Sensory garden timber maintenance | Not started | 018 | |
| 7 | Nature | Elaborate on Green Schools program in application | Not started | 004 | |
| 8 | Nature | More tree planting | Not started | 026 | |
| 9 | Nature | Graveyard extension biodiversity landscaping + Biodiversity Officer | Not started | 019 | TODO: Contact Biodiversity Officer |
| 10 | Sustainability | Water butts for containers | Not started | 010 | |
| 11 | Sustainability | Composting organic waste | Not started | 002 | |
| 12 | Sustainability | Recycle collected litter | Not started | 001 | |
| 13 | Tidiness | Keep mutt mitt dispenser full | Not started | 005 | |
| 14 | Tidiness | Repaint bollards (repeated from 2024) | Not started | 013 | |
| 15 | Residential | Noel Hayes Park bedding + climbers | Not started | 017 | |
| 16 | Residential | Glen Carraig wildflower garden | Not started | 016 | |
| 17 | Residential | Garden competition | Not started | 015 | |
| 18 | Approach Roads | Unmown verge strips for nature | Not started | 009 | |

## MUST DO (immediate)

- [ ] Contact Tipperary Co Co Heritage Officer re: forge window (rec #2)
- [ ] Contact Tipperary Co Co Biodiversity Officer re: graveyard planting (rec #9)
```

- [ ] **Step 3: Create application guide**

Create `private/application-guide.md`:

```markdown
# Application Writing Guide (PRIVATE)

## General Principles

1. **Every category needs substance** - the 2025 Sustainability section was 3 lines. Aim for a full paragraph minimum per category.
2. **Reference specific projects** - name them, describe them, show photos
3. **Include the bog walk** - it was completely missing from 2025
4. **Submit 8-10 attachments** - Emly (395) submitted 10 including reports and map
5. **Include seasonal photographs** - spring, summer, autumn shots show year-round effort
6. **Reference the SDGs** where relevant
7. **Update and submit the 3/5-year plan**
8. **Provide a quality map** with legend and compass points

## Category Tips (from exemplar analysis)

### Community (target: 52+, currently 45)
- Mention ALL committees and groups working together
- Describe the inclusivity event/festival
- Detail school involvement (Green Schools, sensory garden, planting)
- List all communication channels (website, WhatsApp, Instagram, parish leaflet, newspaper)
- Reference the 3/5-year plan
- Name specific volunteer numbers and meeting frequency

### Sustainability (target: 28+, currently 17)
- Describe litter segregation/recycling process
- Detail composting setup and how compost is reused
- Mention water butts and rainwater harvesting
- Reference salvaged timber flower boxes (already doing this!)
- Mention school bike stands (already there!)
- If SEAI grant obtained, describe the energy plan
- Reference eco-friendly weed management
- Mention any food waste awareness activities

### Nature & Biodiversity (target: 38+, currently 29)
- Feature the bog walk and its habitats extensively
- Describe no-mow areas and pollinators.ie approach
- Detail bird boxes, bee hotels in sensory garden
- Reference any wildlife surveys conducted
- Mention Green Schools program connection
- Describe the graveyard extension landscaping plan
- Note any seed saving activities

## Application Checklist

- [ ] All 8 categories completed with substance
- [ ] Map with legend, compass, numbered project references
- [ ] 3/5-year plan attached
- [ ] 8-10 photographs (including seasonal)
- [ ] Bog walk featured prominently
- [ ] Special awards entered (Endeavour, Sustainability, Leave No Trace)
- [ ] Sent to tidytowns@drcd.gov.ie before deadline
- [ ] Under 20MB total email size
```

- [ ] **Step 4: Create photo checklist**

Create `private/photo-checklist.md`:

```markdown
# Pre-Adjudication Photography Checklist (PRIVATE)

Photographs to take across all 4 seasons for application and Instagram.

## Spring (March-April)
- [ ] Daffodils/bluebells on approach roads
- [ ] Early wildflowers emerging in no-mow areas
- [ ] Bog walk after restoration
- [ ] Sensory garden spring planting
- [ ] School garden activities
- [ ] Litter pick volunteers (April blitz)

## Summer (May-July) - BEFORE ADJUDICATION
- [ ] Village centre (monument, shop, pubs, forge)
- [ ] Wildflower areas in full bloom
- [ ] Bog walk loop (both entrances)
- [ ] Sensory garden
- [ ] Church grounds (including wildflower bed if established)
- [ ] All 3 approach roads
- [ ] Housing estates (Harkin Park, Castle Park, Glen Carraig, Noel Hayes Park)
- [ ] Graveyard extension
- [ ] Flower boxes and planters
- [ ] Recycling bank area
- [ ] Water butts (if installed)
- [ ] Composting station (if established)
- [ ] Bird boxes / bee hotels
- [ ] Any new signage
- [ ] Work party / volunteers in action

## Autumn (September-October)
- [ ] Autumn colours along approach roads and bog walk
- [ ] Harvested compost being used in beds
- [ ] End of season garden views

## Winter (December-February)
- [ ] Christmas lights and village crib at forge
- [ ] Winter village streetscape
- [ ] Any winter maintenance work
```

- [ ] **Step 5: Create 3/5-year plan skeleton**

Create `private/3-5-year-plan.md`:

```markdown
# Two Mile Borris TidyTowns 3/5 Year Plan

*To be submitted with the annual TidyTowns application*

## Vision

Two Mile Borris will be a vibrant, sustainable, biodiversity-rich village that celebrates its heritage and welcomes all residents and visitors.

## Year 1 (2026): Foundation

**Focus: Quick wins, bog walk restoration, application quality**

- Establish composting and litter recycling
- Install water butts
- Create wildflower areas (church, Glen Carraig, approach verges)
- Restore bog walk loop surface
- Launch Instagram and seasonal photography
- Contact Heritage Officer and Biodiversity Officer
- Begin wildlife surveys
- Enter Endeavour and Sustainability special awards

## Year 2 (2027): Growth

**Focus: Nature trail, school garden, community engagement**

- Develop bog walk into nature trail with interpretation panels
- Expand school sustainability garden
- Hold first community inclusivity event
- Begin seed saving program
- Apply for SEAI community energy grant
- Develop graveyard biodiversity landscaping
- Enter Leave No Trace special award

## Year 3 (2028): Excellence

**Focus: Heritage trail, integration, medal contention**

- Complete heritage trail linking castle, forge, church, bog walk
- Mature wildflower and biodiversity areas
- Established community events calendar
- Energy master plan developed
- Target county first place and national bronze medal

## Years 4-5 (2029-2030): Consolidation

- Refine and maintain all established projects
- Community food/herb garden
- Rainwater harvesting system
- Target national silver/gold medal
```

- [ ] **Step 6: Commit**

```bash
git add private/
git commit -m "feat: add private application strategy files"
```

---

### Task 11: CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Create CLAUDE.md**

Create `CLAUDE.md`:

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md for Claude Code guidance"
```

---

### Task 12: Generate Remaining Project Pages (39 projects)

**Files:**
- Create: 39 project `index.md` files in `site/docs/projects/`

- [ ] **Step 1: Create a bulk generation script**

Create `scripts/generate-all-projects.sh` that creates all 39 remaining projects from the spec's project list. This is a one-time script.

The script should create each project folder and `index.md` with correct frontmatter (title, tags, status, cost, benefit, special_award) and a description body. All owners and assignees left blank.

Projects to generate (5 already exist from Task 4):
- 004 through 044, skipping 001, 002, 003, 009, 028

Each project needs appropriate tags, status (Tier 1-2 as "Planned 2026", Tier 3 as "Planned 2027", Tier 4 as "Planned 2028"), benefit mapping (marks 5+ = High, 2-4 = Medium, 1 = Low), and a description paragraph.

- [ ] **Step 2: Run the bulk generation script**

```bash
bash scripts/generate-all-projects.sh
```

- [ ] **Step 3: Run generators and verify build**

```bash
bash scripts/generate-index.sh
bash scripts/generate-my-tasks.sh
cd site && uv run --with mkdocs-material mkdocs build 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
git add site/docs/projects/ scripts/generate-all-projects.sh
git commit -m "feat: add all 44 project pages"
```

---

### Task 13: Final Build Verification and Research Commit

- [ ] **Step 1: Full site build and local preview**

```bash
cd site && uv run --with mkdocs-material mkdocs build --strict 2>&1
```

Expected: Clean build, no warnings

- [ ] **Step 2: Commit research data**

```bash
git add research/analysis/ research/extract_scores.py research/compare_reports.py research/reports/
git commit -m "data: add competition research and analysis"
```

Note: The results booklet PDFs in `research/results-booklets/` are large (~50MB total). Consider adding them to `.gitignore` if the repo will be on GitHub free tier, or commit them if storage is not a concern.

- [ ] **Step 3: Commit spec and plan**

```bash
git add docs/
git commit -m "docs: add design spec and implementation plan"
```

- [ ] **Step 4: Verify full repo state**

```bash
git status
git log --oneline
```

Expected: Clean working tree, ~10 commits covering all components.

---

## Post-Build Steps (Manual)

These require manual action outside the repo:

1. **Create GitHub repository** - push local repo to GitHub
2. **Enable GitHub Pages** - Settings > Pages > Source: GitHub Actions
3. **Create Google Forms** - two forms (comment + propose), embed URLs into `submit-idea.md` and `propose-project.md`
4. **Create Instagram account** - @tmbvillage_tidytowns or similar
5. **Share site URL** with committee via WhatsApp
