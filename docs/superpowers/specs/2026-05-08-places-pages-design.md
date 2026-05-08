# Places Pages, Design Spec

## Summary

Give the meaty map markers (heritage, green spaces, school, businesses, the bog walk) their own pages on the public site, sitting under a new "Places" section in the sidebar. Wordy popup descriptions and captions move into proper paragraphs, written by Claude with light web research where village history needs filling in. The map popup gains a "Read more →" link to each place's page; the page links back to the map; project pages and place pages cross-reference each other.

This work also folds Future projects under the existing Projects section so the nav doesn't sprawl.

## Goals

- Give each significant village asset enough room to breathe — readers land on a page, not a popup tooltip
- Replace the current pattern of cramming history/ecology into the marker `desc` field with real prose
- Let visitors and adjudicators move freely between the map, the place pages, and the project pages
- Keep the underlying data (`markers.json`, `_captions.json`) as the single source of truth for photos and coordinates — the new pages reference it, never duplicate it

## Out of scope

- Estates, approach roads, and the new cemetery entrance (no pages — popup only as today; new cemetery entrance content folds into the `cemetery.md` page)
- Any change to project frontmatter beyond adding a single `places` field
- A page-level photo lightbox separate from the map's lightbox (gallery on the page either reuses the map's lightbox or links back to the map)
- Auto-opening map popups from the page side (URL hash deep-linking into the map iframe). The page → map link goes to the map page; clicking the marker is one extra step we accept for v1.

## Navigation change

Update `mkdocs.yml` nav:

```yaml
nav:
  - Home: index.md
  - Projects:
    - Current Projects: projects/index.md
    - Future: future/index.md
    - Completed: completed/index.md
  - Places: places/index.md
  - Village Map: map.md
  - Volunteer: volunteer.md
  - About: about.md
```

Future moves under Projects (was top-level). New top-level Places entry.

## File structure

```
site/docs/places/
  index.md                   ← gateway, places grouped by category
  monument.md
  forge.md
  blackcastle.md
  liathmore.md
  seating_area.md
  black_river.md
  sensory_garden.md
  church.md
  cemetery.md                ← absorbs new_cemetery_entrance content
  old_road_triangle.md
  school.md
  bannons.md
  tullys.md
  corcorans.md
  dempsey_motors.md
  transport_museum.md
  bog_walk.md
```

Flat structure — one file per place, filename = marker_id, predictable URL: `/places/{id}/`.

17 pages total.

## Page template

Frontmatter (minimal, everything else lives in `markers.json`):

```yaml
---
title: "The Blackcastle"
marker_id: blackcastle
category: "Village Features"
hero: castle-streetview-summer.jpg
---
```

- `title` — page title (can override the marker name; e.g. "The Blackcastle" instead of "Blackcastle (Norman Castle)")
- `marker_id` — links the page back to the marker; used by macros to find photos and inject the "Show on map" footer
- `category` — same string as in `markers.json`; used by `place_list_by_category` for grouping
- `hero` — filename (within `photos/{marker_id}/`) of the hero image; defaults to the first photo in `_captions.json` if omitted

Body structure:

1. Hero photo with caption (auto-rendered from frontmatter `hero` + caption from `_captions.json`)
2. **Prose** — 2–4 paragraphs in the committee voice (the meat of the page)
3. Photo gallery rendered by `{{ place_photos("monument") }}` macro
4. Auto-rendered footer: "← Show on map" + Related projects (if any)

## Macros (additions to `site/main.py`)

### `place_list_by_category()`

Scans `places/*.md`, reads frontmatter, groups by `category`, renders the index page. Same shape as `project_list_by_year()`. Output is a markdown section per category with a card or table of places (title + thumbnail + 1-line teaser pulled from `markers.json` desc).

### `place_photos(marker_id)`

Reads `site/docs/assets/map-data/photos/{marker_id}/_captions.json`, renders an HTML grid of thumbnails with captions. On click, opens the same lightbox UX as the map (or, simpler: links to `/map.md` and lets the visitor click the marker — TBD during implementation, pick whichever is less code).

### `on_post_page_macros` hook (extension)

Add a branch: if `src_path` matches `places/*.md`, append:

- `**Category:** {category}` line
- "← Show on map" link to `/map.md`
- Related projects: scan `projects/*/index.md` and `future/*/index.md` for any with `places: [marker_id, ...]` in frontmatter, render as a list

## Map popup changes

In `site/docs/assets/map-template.html` `buildPopup()`:

- If the marker has a `page_url` field, render a "Read more →" button alongside the existing "Open in Google Maps" button
- Button styling: same shape as the gmaps button, different colour (e.g. green to match the site theme)

In `scripts/build_map.py`:

- After loading photos, also check whether `site/docs/places/{marker_id}.md` exists
- If it does, set `marker["page_url"] = f"../places/{marker_id}/"` (relative path that works from the map iframe served at `/assets/village-map.html`)

In `markers.json`:

- For markers that get a page, shorten `desc` to a 1-line teaser. The full content lives on the page now.
- Markers without pages keep their current `desc` unchanged.

## Project ↔ place linking

Add a `places` field to project frontmatter (optional, list of marker_ids):

```yaml
---
title: "Install water butts for watering containers and baskets"
delivery_year: 2026
places:
  - church
  - monument
...
---
```

Render on project pages (extend the existing `on_post_page_macros` hook for project pages):

- After the metadata bar, append: "**Places:** [Church](../../places/church.md), [Monument Area](../../places/monument.md)"

Render on place pages (new branch in the hook):

- Append "**Related projects:** [Install water butts...](../projects/010-water-butts/index.md), ..."

A simple, symmetric relationship. No DB, no IDs to keep in sync — just frontmatter scanning.

Initial population: when writing each place page, sweep `projects/` and `future/` for projects that reference that place (water butts → church, bollard repaint → monument, biodiversity landscaping → cemetery, wildflower → glen_carraig but glen_carraig is an estate so no page) and add the `places` field to those project files.

## Scaffold script

`scripts/new-place.py`:

```bash
uv run python scripts/new-place.py <marker_id>           # one stub
uv run python scripts/new-place.py --all                 # all 17 stubs at once
```

Reads `markers.json`, generates the .md file with frontmatter pre-filled (title from `name`, category from `category`, hero from first photo in `_captions.json`), with placeholder body section so Claude/the user can fill in prose. Skips if file already exists (use `--force` to overwrite).

## Content / prose strategy

Claude writes all 17 prose bodies in the existing committee voice (warm, casual volunteer tone; no em-dashes; colourful Hiberno-English; no Latin names; no theatre metrics). Two tiers by research need:

**No research needed** — pull from existing captions/desc and expand:
- monument (1900 hurling history is already in captions)
- forge
- seating_area
- black_river
- sensory_garden
- church (history light, mostly current/projects)
- old_road_triangle (rich captions already)
- bannons, tullys, corcorans (light, mostly current)
- dempsey_motors (covered by memory + current photos)
- transport_museum (light)
- bog_walk (rich captions)

**Light web research needed** — Claude does ~1–3 quick searches per place:
- blackcastle — confirm 12th vs 16th century (existing content has both); known builders if any; classification (tower house vs hall-house); sources to check: Buildings of Ireland (NIAH), Tipperary County Council heritage register, Wikipedia, megalithicireland.com
- liathmore — St Mochoemog founding date, sheela-na-gig provenance, Romanesque doorway dating; sources: Heritage Council, Wikipedia, archaeology.ie
- school — confirm 1846 founding from the cast plaque, any catchment/historical names; sources: scoilmochaomhog.ie, Department of Education historical records
- cemetery — when consecrated, any notable burials, history of the new extension; sources: Tipperary heritage records
- monument (1900 GAA detail) — verify match details, panel members already on plaque; sources: GAA archives (light cross-check, plaque is authoritative)

Claude flags any uncertain claim with an inline TODO comment so the user can verify before publishing. No invention of facts.

## Implementation phases

Suggested split for executing (will be refined in the implementation plan):

1. **Infrastructure** — nav change, `places/` directory, scaffold script, macros, map popup changes, hook extensions. Validates the plumbing end-to-end with one or two stub pages.
2. **Easy content** — write the ~12 places that don't need research.
3. **Research-led content** — write the ~5 places that need web research.
4. **Project ↔ place linking** — add `places:` frontmatter to relevant project files; verify rendering on both sides.
5. **Polish** — proofread, prune duplicate content from `markers.json` `desc` fields, build, eyeball.

## Risks / tradeoffs

- **Maintenance burden** — 17 prose pages is more content to keep current than a single map. Mitigated by: pages focus on durable history/ecology/character (rarely changes); current operational status stays in projects/ where it's already kept up.
- **Duplication of `desc`** — risk of drift between `markers.json` `desc` and the place page intro. Mitigated by deliberately shortening `desc` to a 1-line teaser that doesn't repeat what's on the page.
- **Estates exclusion** — readers might wonder why estates aren't clickable to a page. Mitigated by clear category cues (the legend distinguishes them); estate popups remain informative as today.
- **Light-content pages** — pubs and the transport museum may end up with thin content. Acceptable: a short page is fine if the photos do the work, and it's still better than burying the photos in a popup.
