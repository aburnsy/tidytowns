# TMB Tidy Towns Strategy Platform - Design Spec

## Overview

A GitHub Pages website and local project toolkit for Two Mile Borris Tidy Towns to:
1. **Manage projects & tasks** - projects are projects the committee decides on; tasks are the work within them, assigned to volunteers with dates
2. **Volunteer task view** - any volunteer can filter to see their assigned tasks across all projects
3. **Collect community ideas** via embedded Google Forms (project comments + new project proposals)
4. **Privately prepare** annual competition applications
5. **Store research data** (results analysis, exemplar reports, score tracking)
6. **Reference best practices** - biodiversity work backed by pollinators.ie, sustainability by SEAI guidelines, etc.

## Current Position

- **Score**: 318/550 (58%) - Category B, Tipperary North
- **Target**: County winner (~380+) in 3 years, national Category B medal (~390+) in 5 years
- **Budget**: ~€1k this year, ~€2k next year, €10k max per project
- **Volunteers**: 20-50 person-hours/month from 27 committee + 5 volunteers

## Architecture

```
tidytowns/
├── docs/                          # Design specs (this file)
├── research/                      # Data & analysis (NOT published)
│   ├── results-booklets/          # Downloaded PDF results books
│   ├── reports/                   # Adjudication reports (TMB + exemplars)
│   └── analysis/                  # Extracted scores, comparisons, jumps
├── site/                          # GitHub Pages source (PUBLISHED)
│   ├── mkdocs.yml                 # MkDocs Material config
│   ├── docs/
│   │   ├── index.md               # Homepage - all projects, filterable
│   │   ├── projects/              # One folder per project
│   │   │   ├── 001-segregate-litter/
│   │   │   │   ├── index.md       # Project page (description, owner, status, form link)
│   │   │   │   ├── task-buy-bags.md       # Task with assignees & date
│   │   │   │   └── task-brief-volunteers.md
│   │   │   ├── 002-composting/
│   │   │   │   ├── index.md
│   │   │   │   └── task-source-bin.md
│   │   │   └── ...
│   │   ├── my-tasks.md            # Volunteer task view (filter by name)
│   │   ├── progress.md            # Score tracking & targets
│   │   ├── submit-idea.md         # Google Form: comment on a project
│   │   ├── propose-project.md     # Google Form: propose a new project
│   │   └── about.md               # About TMB Tidy Towns
│   └── overrides/                 # Theme customisation
├── private/                       # Application strategy (NOT published)
│   ├── application-guide.md       # Category-by-category writing guide
│   ├── adjudicator-tracker.md     # Recommendations status tracker
│   ├── photo-checklist.md         # Pre-adjudication photography list
│   └── 3-5-year-plan.md           # Formal plan for submission
├── applications/                  # Historical applications
│   └── 2025-SuperValu-TidyTowns-Entry-Form-English.docx
├── CLAUDE.md                      # Claude Code guidance
└── .github/
    └── workflows/
        └── deploy.yml             # GitHub Actions to build & deploy site
```

## Public Site (GitHub Pages via MkDocs Material)

### Technology
- **MkDocs Material** - static site generator with built-in search, tags, and professional appearance
- **GitHub Actions** - auto-deploy on push
- **Google Forms** - embedded for idea submission (submit-only, no login required)

### Projects (the "what")

Each project is a folder with an `index.md` and task files. The project `index.md` has:

```yaml
---
title: "Segregate collected litter into recyclables"
tags:
  - sustainability
  - tidiness
status: "Planned 2026"        # Will Do | Won't Do | Planned YYYY | Under Discussion
owner: "Michael M"            # Overall project owner (shortname)
cost_estimate: "€0"
benefit: "High"               # High | Medium | Low (PUBLIC - derived from private marks estimate)
volunteer_hours: "2hrs setup, then ongoing (15 min per cleanup)"
inspired_by: "Adjudicator 2025 recommendation"
special_award: ""             # If targeting a special award, name it here
references:
  - title: "All-Ireland Pollinator Plan"
    url: "https://pollinators.ie"
---

## Description
...

## What the adjudicator said
...

## Best practice & research
Links to pollinators.ie, SEAI guidelines, etc. as relevant to this project.

## Tasks
Auto-listed from task files in this folder.

## Have your say
[Comment on this project](../submit-idea.md) | [Propose a new project](../propose-project.md)
```

### Public vs Private Language

The public site **never mentions marks, points, or scoring**. It frames everything as community improvement.

| Private (in `private/` folder) | Public (on site) |
|---|---|
| marks_estimate: "+3-5" | benefit: "High" |
| marks_per_euro: "Infinite" | cost_estimate: "€0" |
| "Close the gap in Sustainability" | "Improve our environmental impact" |
| "Adjudicator recommended" | "Recommended for our village" |

**Benefit mapping:**
- **High** = estimated +5 or more marks
- **Medium** = estimated +2 to +4 marks
- **Low** = estimated +1 mark

The private `adjudicator-tracker.md` and research files contain the actual marks analysis. These are never published.

### Tasks (the "how")

Tasks live as markdown files inside their project folder. Each task has:

```yaml
---
title: "Source and purchase recycling bags"
status: "pending"              # pending | in_progress | done
assignees:
  - "Andy B"
  - "Mary Q"
due_date: "2026-06-01"
tags:
  - sustainability
---

Buy 3 rolls of colour-coded recycling bags for litter cleanup segregation.
```

### Status Values

**Project statuses:**
- **Planned 2026** / **Planned 2027** / **Planned 2028** - scheduled for a specific year
- **Will Do** - approved but not yet scheduled
- **Won't Do** - considered and rejected (with reason). **Hidden by default** on the site (accessible via filter but not in the main project list)
- **Under Discussion** - awaiting committee input

**Task statuses:**
- **pending** - not started
- **in_progress** - underway
- **done** - completed (updated weekly via repo)

### Volunteer View (`my-tasks.md`)

A page where any volunteer can search/filter their shortname to see all tasks assigned to them across all projects. Shows: task title, project it belongs to, due date, status, and who else is assigned.

No PII - shortnames only (first name + last initial, e.g. "Andy B", "Mary Q").

### Research & Best Practice References

Projects in specific categories should reference authoritative sources:
- **Biodiversity**: [pollinators.ie](https://pollinators.ie) - All-Ireland Pollinator Plan guidelines
- **Sustainability**: SEAI community energy resources
- **Heritage**: Heritage Council / Tipperary Heritage Officer guidance
- **Green Spaces**: Teagasc native planting guides

These are linked per-project in the `references` frontmatter field.

### Filterable Homepage
MkDocs Material's tags plugin allows filtering by:
- Category tags (sustainability, nature-biodiversity, streetscape, etc.)
- Status (via search or tag)
- Each project card shows: title, status badge, cost, estimated marks

### Google Forms (two forms)

**1. Comment on a project (`submit-idea.md`)**
- Fields: Your name (optional), Which project? (dropdown), Your idea/comment, Location in village (optional)
- Linked from every project page
- Responses go to a private Google Sheet

**2. Propose a new project (`propose-project.md`)**
- Fields: Your name (optional), Project idea, Which category? (dropdown: Sustainability / Nature & Biodiversity / Streetscape / etc.), Why is it important?, Estimated cost (optional), Location (optional)
- Linked from the homepage and nav
- Responses go to the same or a separate Google Sheet

Both forms are submit-only. No login. Only Andre sees responses.

### Progress Page
- Current scores vs targets
- Year-on-year comparison chart (text-based table)
- Gap analysis vs county competitors

## Private Application Strategy (`private/`)

Not deployed to GitHub Pages. Contains:

### `application-guide.md`
Category-by-category guide with:
- What adjudicators look for (from judging criteria + exemplar analysis)
- Template paragraphs referencing TMB projects
- Common mistakes (e.g. Sustainability section was 3 lines in 2025)
- Tips from high-scoring villages (Emly, Silvermines)

### `adjudicator-tracker.md`
Table tracking every recommendation from prior years:

| Year | Category | Recommendation | Status | Action Taken |
|---|---|---|---|---|
| 2025 | Streetscape | Paint derelict openings + window boxes | Not started | |
| 2025 | Streetscape | Replica window in forge | Not started | Contact Heritage Officer |
| 2025 | Green Spaces | Pollinator Plan species | Not started | |
| ... | ... | ... | ... | ... |

### `photo-checklist.md`
Pre-adjudication (May/June) photography shot list:
- Each project site, before and after
- Seasonal photos (spring daffodils, summer wildflowers, autumn colours, winter)
- Bog walk in good condition
- Community events/work parties
- School garden activities

### `3-5-year-plan.md`
Formal plan document to submit with application, structured by year with targets.

## Project List (42 projects)

### Tier 1: Near-Zero Cost (€0-€100) - 15 projects
1. Segregate collected litter | Sustainability | €0 | +3-5
2. Composting for beds | Sustainability | €50-80 | +3-4
3. Feature bog walk in application | Multiple | €0 | +5-8
4. Green Schools elaboration | Nature | €0 | +1-2
5. Keep mutt mitt stocked | Tidiness | €20/yr | +1
6. Better application writing | All | €0 | +5-10
7. Contact Heritage Officer | Streetscape | €0 | +1-2
8. Contact Biodiversity Officer | Nature | €0 | +1-2
9. Unmown verge strips | Nature | €0 | +2-3
29. Seed saving program | Nature + Sust | €20-50 | +2-4
35. Seasonal photography | All | €0 | +3-5
38. SDG integration in application | Community + Sust | €0 | +2-3
39. Slan Abhaile signs | Approach Roads | €50-100 | +1-2
43. Create Tidy Towns Instagram account | Community | €0 | +2-3
44. Seasonal photography program (4 seasons) | All categories | €0 | +3-5

### Tier 2: Low Cost (€100-€500) - 13 projects
10. Water butts (2-3) | Sustainability | €100-150 | +2-3
11. Wildflower bed at church (no-mow + signage) | Green + Nature | €0-50 (signage only) | +3-4
12. Pollinator Plan species | Green + Nature | €100-200 | +3-5
13. Repaint bollards | Tidiness | €30-50 | +1-2
14. Derelict property: paint + boxes | Streetscape | €100-200 | +2-3
15. Garden competition | Residential | €100 | +2-3
16. Glen Carraig wildflower area (no-mow + signage) | Residential + Nature | €0-50 (signage only) | +2-3
17. Noel Hayes Park bedding | Residential | €150-300 | +2-3
18. Sensory garden maintenance | Green Spaces | €100-200 | +2-3
32. Community inclusivity event | Community | €200-500 | +3-5
34. Paint vacant buildings vibrant | Streetscape | €200-500 | +3-5
40. Eco-friendly weed management | Sustainability + Tidiness | €50-100 | +2-3
42. Food waste workshop | Sustainability | €50-200 | +2-3

### Tier 3: Medium Cost (€500-€2,000) - 9 projects
19. Graveyard biodiversity landscaping | Nature | €500-1,500 | +4-6
20. Heritage interpretation panels | Streetscape + Comm | €500-1,000 | +3-5
21. 3/5-year plan document | Community | €0 (time) | +3-5
22. Forge replica window | Streetscape | €500-2,000 | +2-4
23. Bog walk biodiversity signage | Nature + Green | €500-1,000 | +3-5
30. Wildlife info panels (3-4 spots) | Nature | €300-600 | +4-6
37. Wildlife surveys (bird, pollinator) | Nature | €0-200 | +3-5
41. Knowledge sharing with other TT | Community | €0-100 | +2-3
36. Apply for SEAI energy grant | Sustainability | €0 | +3-5

### Tier 4: Long-term Showcase (€2,000-€10,000) - 7 projects
24. Community food/herb garden | Sust + Comm | €2,000-5,000 | +5-8
25. Heritage trail (castle-forge-church-bog walk) with signage & map | Street + Comm | €3,000-8,000 | +5-10
26. Biodiversity corridor/tree planting | Nature | €1,000-3,000 | +4-7
27. Rainwater harvesting system | Sustainability | €2,000-5,000 | +3-5
28. Bog walk nature trail transformation | Nature + Green + Comm | €1,000-3,000 | +8-15
31. School sustainability showcase | Sust + Nature | €500-1,500 | +5-8

## Special Awards to Target

Separate from the main competition - voluntary entry, additional cash prizes. TMB should target:

| Award | Prize | TMB Fit | Notes |
|---|---|---|---|
| **Endeavour Award** | €500 | Excellent | Biggest % improvement in county. Very achievable given TMB's low base and planned jump. |
| **Sustainability & Circular Economy** | €1,000 (1st) | Strong | Aligns with our biggest gap. Composting, recycling, water butts, SEAI grant. |
| **Leave No Trace** | €1,000 + trainer day | Strong | Bog walk + nature trail + biodiversity work. |
| **Inclusion Award** | €2,000 | Good | Community event/festival involving new residents, all ages, nationalities. |
| **Active Travel** | TBC (new 2025) | Possible | School bike stands, footpaths, bog walk as walking amenity. |
| **Tiny TidyTowns** | TBC (new 2025) | Good | School already involved - sensory garden, Green Schools. |

Each eligible project should be tagged with `special_award` in its frontmatter so we track which projects contribute to which special award entries.

## Instagram Strategy

Create **@tmbvillage_tidytowns** (or similar) as a dedicated Tidy Towns Instagram:

- **Purpose**: Document work, build seasonal photo library for applications, engage community, show adjudicators a strong digital presence
- **Content**: Before/after project photos, volunteer work parties, wildlife/nature shots from bog walk, seasonal village views, event coverage
- **Frequency**: 2-3 posts per week during active season (April-September), 1 per week off-season
- **Benefits for competition**: Silvermines was praised for social media video clips; Emly for extensive communication channels. This directly supports the Community category.
- **Practical**: One committee member owns the account. Content can be reused in the application.

This is a zero-cost project that supports marks across Community (communication channels) and provides the seasonal photography needed for a strong application.

**Instagram and seasonal photography are both standalone projects in the project list** (see projects 43 and 44 below).

## Biodiversity Best Practice (pollinators.ie)

All biodiversity and wildflower projects must follow the All-Ireland Pollinator Plan guidelines:

1. **Don't sow commercial wildflower seed mixes** - they are often non-native and can outcompete local species
2. **Reduce/stop mowing** in selected areas first - allow the existing seed bank in the soil to emerge naturally
3. **Only sow if needed**, and use **native, locally-sourced seed** (e.g. Yellow Rattle to suppress grasses)
4. **Install "managed for wildlife" signage** - unmown areas can look neglected without context; signage explains the purpose and impresses adjudicators
5. **Cost is near-zero** (less than mowing!) - budget is primarily for signage

This means wildflower projects (church, Glen Carraig, approach verges) are essentially free to implement. The cost estimates on those projects are for signage and minor native seed if needed, not commercial seed mixes.

## CLI Scripts

Two interactive scripts to guide adding content without manually writing frontmatter:

### `scripts/new-project.sh`
Walks through creating a new project:
1. Project title
2. Category tags (multi-select from the 8 categories)
3. Status (Planned YYYY / Will Do / Under Discussion)
4. Owner (shortname, or leave blank)
5. Cost estimate
6. Benefit level (High/Medium/Low)
7. Description
8. Special award targeting (optional)
9. References (optional)

Generates the folder + `index.md` with correct frontmatter.

### `scripts/new-task.sh`
Walks through creating a task within a project:
1. Select project (lists existing projects)
2. Task title
3. One-off or recurring? 
   - If recurring: frequency (weekly / bi-monthly / monthly / seasonal) and active months (e.g. "Apr-Sep")
4. Assignees (comma-separated shortnames, or leave blank)
5. Due date (for one-off) or start date (for recurring)
6. Description

Generates the task `.md` file in the correct project folder.

### `scripts/generate-recurring.sh`
Reads all tasks with `recurring` set and generates concrete dated task files for the next 3 months. Run this monthly (or whenever you want to plan ahead). Example:

A recurring task template:
```yaml
---
title: "Check no-mow areas - remove dock leaves & thistles"
status: "template"
recurring: "monthly"
active_months: "Apr-Sep"     # Only generate during growing season
assignees:
  - "Andy B"
tags:
  - nature-biodiversity
---
Walk no-mow areas (church, Glen Carraig, approach verges).
Remove dock leaves and thistles by hand (pollinators.ie guideline).
Leave all other growth undisturbed.
```

Running `generate-recurring.sh` creates:
- `task-dock-check-2026-04.md` (status: pending, due: 2026-04-30)
- `task-dock-check-2026-05.md` (status: pending, due: 2026-05-31)
- `task-dock-check-2026-06.md` (status: pending, due: 2026-06-30)

Skips months outside `active_months` and doesn't regenerate tasks that already exist.

### Recurring task examples across projects

| Project | Recurring Task | Frequency | Active Months |
|---|---|---|---|
| No-mow wildflower areas | Remove dock leaves & thistles | Monthly | Apr-Sep |
| Sensory garden maintenance | Timber/pathway inspection & repair | Bi-monthly | Mar-Oct |
| Mutt mitt dispenser | Restock bags | Bi-monthly | Year-round |
| Litter control | Village litter pick | Monthly | Year-round |
| Flower boxes/planters | Water & weed containers | Weekly | May-Sep |
| Composting | Turn compost, check bins | Monthly | Year-round |
| Instagram | Post update photos | Weekly | Year-round |
| Bog walk | Path condition check & clearance | Monthly | Mar-Oct |

## Implementation Approach

### Phase 1: Repository & Site Setup
- Initialize git repo
- Set up MkDocs Material with tags plugin
- Create `scripts/new-project.sh` and `scripts/new-task.sh` guided CLI tools
- Write all 42 project pages (owner and assignees left **blank** initially - committee assigns later)
- Create both Google Forms (project comments + new project proposals)
- Set up GitHub Actions deploy pipeline
- Deploy to GitHub Pages
- Create CLAUDE.md
- Create Instagram account (manual - Andre does this)

### Phase 2: Private Application Strategy
- Write application guide
- Create adjudicator tracker
- Create photo checklist
- Draft 3/5-year plan

### Phase 3: Research Archive
- Commit downloaded results booklets and reports
- Commit analysis scripts and outputs
- Write research summary

## Scoring Targets

| Year | Target Score | Key Actions |
|---|---|---|
| 2026 | ~365 | Quick wins (Tier 1 + some Tier 2) + bog walk + application excellence |
| 2027 | ~385 | Nature trail matures, wildlife surveys, school garden, SEAI grant |
| 2028 | ~400+ | Heritage trail, festival established, energy plan, medal contention |

## Future Research Expansion (TODO)

The current research covers:
- 6 years of results booklets (2019-2025)
- 1,622 Category B entries extracted
- 4 exemplar village reports analysed in detail

**Long-term goal: comprehensive multi-year analysis of every village in Tipp North, Tipp South, and all Category B nationally.** This means:
- Download and parse ALL individual adjudication reports (not just booklet scores) for Tipp North/South villages across 5+ years
- Track what specific projects each competitor village undertook and how their scores changed
- Identify which project types consistently correlate with the biggest score jumps
- Build a searchable database of ideas harvested from hundreds of reports
- Monitor competitor trajectories year-on-year to anticipate where TMB needs to be

**Our AI advantage**: TMB is using AI to systematically analyse competition data, extract project ideas from hundreds of adjudication reports, and optimise strategy. Other villages rely on intuition and word of mouth. This data-driven approach is our edge - we should expand it aggressively.

## Notes
- From 2026, Nature & Biodiversity and Sustainability both increase to 80 marks (from 55), total becomes 600. This makes those categories even more critical.
- Emly got a **second round adjudication** at 395 - that's the level where you get noticed nationally.
- The bog walk is TMB's biggest untapped asset - not even mentioned in the 2025 application.
