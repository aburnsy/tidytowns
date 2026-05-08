# Places Pages, Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give 17 significant village markers their own pages on the public site under a new "Places" section, with prose written in the committee voice (with light web research where village history needs filling in), bidirectional map ↔ place linking, and project ↔ place cross-references.

**Architecture:** Flat `site/docs/places/{marker_id}.md` structure mirroring the projects pattern. Page content is hand-written prose; photos and coordinates stay in `markers.json` and `_captions.json` (single source of truth). Two new mkdocs-macros (`place_list_by_category`, `place_photos`) plus an extension to the existing `on_post_page_macros` hook render the pages and cross-references. `build_map.py` injects a `page_url` field for markers that have a page; the map popup gains a "Read more →" button.

**Tech Stack:** mkdocs-material, mkdocs-macros-plugin (Python), Leaflet.js (existing map), vanilla HTML/CSS/JS for the map template.

**Spec:** `docs/superpowers/specs/2026-05-08-places-pages-design.md`

**Testing approach:** No unit tests in this codebase. Verification = `mkdocs serve` and visual inspection. Each task ends with a `mkdocs build` (no errors) and a one-line description of what to eyeball in the dev server.

**Commit policy:** Commit after each cluster of related tasks (suggested commit points marked). Do not commit individual content pages — wait for the full cluster to be reviewed.

---

## Phase 1: Infrastructure

### Task 1: Restructure nav (move Future under Projects, add Places)

**Files:**
- Modify: `site/mkdocs.yml`

- [ ] **Step 1: Update the nav block**

Replace the existing `nav:` section in `site/mkdocs.yml` with:

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

- [ ] **Step 2: Verify mkdocs accepts the config**

Run from the `site/` directory:

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build --strict 2>&1 | head -30
```

Expected: build will fail with "page 'places/index.md' missing" — that's fine for now, it confirms the nav was parsed and the only error is the missing file we're about to create.

### Task 2: Create `places/index.md` skeleton

**Files:**
- Create: `site/docs/places/index.md`

- [ ] **Step 1: Write the index page**

Create `site/docs/places/index.md`:

```markdown
---
title: Places in Two Mile Borris
---

# Places

The corners of Two Mile Borris worth a longer look. Heritage spots that go back centuries, the green spaces we look after week to week, the businesses on the main street, the school at the heart of the village, and the bog walk loop out the back of it all.

For the lay of the land, head over to the [village map](../map.md). For the projects we have on the go at each spot, the [project tracker](../projects/index.md) is the place to look.

{{ place_list_by_category() }}
```

- [ ] **Step 2: Run build (will still fail until macro exists)**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build --strict 2>&1 | head -30
```

Expected: build will now fail on undefined `place_list_by_category` macro — proceed to Task 3 to add it.

### Task 3: Add `place_list_by_category` macro to `main.py`

**Files:**
- Modify: `site/main.py`

- [ ] **Step 1: Add a helper to scan `places/` directory**

Add this function to `site/main.py` after the existing `_scan_dir` function (around line 80):

```python
def _scan_places(docs_dir):
    """Scan places/*.md and return list of place dicts with metadata."""
    base = Path(docs_dir) / "places"
    places = []
    if not base.exists():
        return places
    for md_file in sorted(base.iterdir()):
        if not md_file.is_file() or md_file.suffix != ".md":
            continue
        if md_file.name == "index.md":
            continue
        meta, body = _read_frontmatter(str(md_file))
        meta["_filename"] = md_file.stem
        meta["_body"] = body
        places.append(meta)
    return places
```

- [ ] **Step 2: Add a helper to load marker data from markers.json**

Add this function to `site/main.py` near `_scan_places`:

```python
def _load_markers(docs_dir):
    """Load markers.json and return {marker_id: marker_dict}."""
    import json
    markers_file = Path(docs_dir) / "assets" / "map-data" / "markers.json"
    if not markers_file.exists():
        return {}
    with open(markers_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    by_id = {m["id"]: m for m in data.get("markers", [])}
    bog = data.get("bogWalk")
    if bog:
        by_id["bog_walk"] = {
            "id": "bog_walk",
            "name": bog.get("name", "Bog Walk Loop"),
            "category": bog.get("category", "Bog Walk"),
            "color": bog.get("color", "#1B5E20"),
            "desc": bog.get("description", ""),
        }
    return by_id
```

- [ ] **Step 3: Register the `place_list_by_category` macro**

Add inside the `define_env(env)` function in `site/main.py`, alongside the other `@env.macro` blocks:

```python
    @env.macro
    def place_list_by_category():
        """Render places grouped by category as cards/links."""
        docs_dir = env.conf["docs_dir"]
        places = _scan_places(docs_dir)
        markers = _load_markers(docs_dir)

        src_path = env.page.file.src_path.replace("\\", "/")
        prefix = "" if src_path.startswith("places/") else "places/"

        # Order categories the same way the map legend does
        category_order = [
            "Village Features",
            "Green Spaces & Nature",
            "School",
            "Businesses",
            "Bog Walk",
            "Other",
        ]
        by_category = defaultdict(list)
        for p in places:
            by_category[p.get("category", "Other")].append(p)

        lines = []
        for cat in category_order:
            if cat not in by_category:
                continue
            lines.append(f"## {cat}\n")
            for p in sorted(by_category[cat], key=lambda x: x.get("title", x["_filename"])):
                title = p.get("title", p["_filename"])
                fname = p["_filename"]
                marker_id = p.get("marker_id", fname)
                marker = markers.get(marker_id, {})
                teaser = marker.get("desc", "")
                # Truncate teaser to one sentence / 140 chars
                if len(teaser) > 140:
                    teaser = teaser[:137].rsplit(" ", 1)[0] + "…"
                lines.append(f"- **[{title}]({prefix}{fname}.md)** — {teaser}")
            lines.append("")
        return "\n".join(lines)
```

- [ ] **Step 4: Verify build still parses (will fail because place files don't exist yet, but macro should be registered)**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | head -20
```

Expected: build succeeds (no places yet, so the index renders empty under category headers — that's fine for now).

**Suggested commit point:** "scaffold places nav and index page" (Tasks 1-3 together).

---

### Task 4: Create scaffold script `scripts/new-place.py`

**Files:**
- Create: `scripts/new-place.py`

- [ ] **Step 1: Write the scaffold script**

Create `scripts/new-place.py`:

```python
"""Scaffold a place page (or all of them) from markers.json.

Usage:
  uv run python scripts/new-place.py <marker_id>          # one place
  uv run python scripts/new-place.py --all                # all eligible places
  uv run python scripts/new-place.py <marker_id> --force  # overwrite existing
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACES_DIR = ROOT / "site" / "docs" / "places"
MARKERS_JSON = ROOT / "site" / "docs" / "assets" / "map-data" / "markers.json"
PHOTOS_DIR = ROOT / "site" / "docs" / "assets" / "map-data" / "photos"

# Markers that get pages (everything except estates, approach roads,
# and the new cemetery entrance which folds into cemetery.md)
ELIGIBLE = {
    "monument", "forge", "blackcastle", "liathmore", "seating_area", "black_river",
    "sensory_garden", "church", "cemetery", "old_road_triangle",
    "school",
    "bannons", "tullys", "corcorans", "dempsey_motors",
    "transport_museum",
    "bog_walk",
}


def first_photo(marker_id: str) -> str:
    captions_file = PHOTOS_DIR / marker_id / "_captions.json"
    if not captions_file.exists():
        return ""
    try:
        with open(captions_file, "r", encoding="utf-8") as f:
            entries = json.load(f)
        if entries:
            return entries[0].get("file", "")
    except (json.JSONDecodeError, OSError):
        pass
    return ""


def load_data():
    with open(MARKERS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    by_id = {m["id"]: m for m in data["markers"]}
    bog = data.get("bogWalk")
    if bog:
        by_id["bog_walk"] = {
            "id": "bog_walk",
            "name": bog.get("name", "Bog Walk Loop"),
            "category": bog.get("category", "Bog Walk"),
        }
    return by_id


def scaffold(marker_id: str, by_id: dict, force: bool = False) -> bool:
    if marker_id not in ELIGIBLE:
        print(f"  skip {marker_id} (not in eligible set)")
        return False
    if marker_id not in by_id:
        print(f"  skip {marker_id} (not in markers.json)")
        return False

    out = PLACES_DIR / f"{marker_id}.md"
    if out.exists() and not force:
        print(f"  skip {marker_id} (already exists)")
        return False

    m = by_id[marker_id]
    title = m.get("name", marker_id)
    category = m.get("category", "Other")
    hero = first_photo(marker_id)

    fm_lines = ["---", f'title: "{title}"', f"marker_id: {marker_id}",
                f'category: "{category}"']
    if hero:
        fm_lines.append(f"hero: {hero}")
    fm_lines.append("---")

    body = f"""
[TODO: 2-4 paragraphs of prose in the committee voice]

{{{{ place_photos("{marker_id}") }}}}
"""

    out.write_text("\n".join(fm_lines) + body, encoding="utf-8")
    print(f"  wrote {out.relative_to(ROOT)}")
    return True


def main():
    args = sys.argv[1:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]

    PLACES_DIR.mkdir(parents=True, exist_ok=True)
    by_id = load_data()

    if not args:
        print("usage: new-place.py <marker_id> | --all  [--force]")
        sys.exit(1)

    if args[0] == "--all":
        for mid in sorted(ELIGIBLE):
            scaffold(mid, by_id, force=force)
    else:
        for mid in args:
            scaffold(mid, by_id, force=force)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the script to scaffold all 17 places**

```bash
uv run python scripts/new-place.py --all
```

Expected output: "wrote site/docs/places/bannons.md" etc. for all 17 files. Re-running prints "skip ... (already exists)".

- [ ] **Step 3: Verify the files were created**

```bash
ls site/docs/places/
```

Expected: index.md plus 17 marker stubs (bannons.md, black_river.md, blackcastle.md, bog_walk.md, cemetery.md, church.md, corcorans.md, dempsey_motors.md, forge.md, liathmore.md, monument.md, old_road_triangle.md, school.md, seating_area.md, sensory_garden.md, transport_museum.md, tullys.md).

### Task 5: Add `place_photos` macro to `main.py`

**Files:**
- Modify: `site/main.py`

- [ ] **Step 1: Add the macro**

Add inside `define_env(env)` in `site/main.py`, alongside the other `@env.macro` blocks:

```python
    @env.macro
    def place_photos(marker_id, limit=None):
        """Render a photo grid for a place from _captions.json.

        Photos link to the full-size image (browser handles the view).
        Pages can pass `limit` to cap the number rendered.
        """
        import json
        docs_dir = env.conf["docs_dir"]
        captions_file = Path(docs_dir) / "assets" / "map-data" / "photos" / marker_id / "_captions.json"
        if not captions_file.exists():
            return ""
        try:
            with open(captions_file, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except (json.JSONDecodeError, OSError):
            return ""
        if not entries:
            return ""

        # Skip the hero (first photo) since it's already rendered above the prose
        entries = entries[1:]
        if limit is not None:
            entries = entries[:limit]
        if not entries:
            return ""

        src_path = env.page.file.src_path.replace("\\", "/")
        prefix = "../" if src_path.startswith("places/") else ""
        photo_base = f"{prefix}assets/map-data/photos/{marker_id}"

        items = ['<div class="place-gallery">']
        for entry in entries:
            file = entry.get("file", "")
            caption = entry.get("caption", "").replace('"', "&quot;")
            if not file:
                continue
            items.append(
                f'<figure class="place-photo">'
                f'<a href="{photo_base}/{file}" target="_blank" rel="noopener">'
                f'<img src="{photo_base}/{file}" alt="{caption}" loading="lazy" />'
                f'</a>'
                f'<figcaption>{entry.get("caption", "")}</figcaption>'
                f'</figure>'
            )
        items.append("</div>")
        return "\n".join(items)
```

- [ ] **Step 2: Add gallery CSS to `extra.css`**

Append to `site/docs/stylesheets/extra.css` (create if doesn't exist):

```css
/* Place page photo gallery */
.place-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin: 24px 0;
}
.place-photo {
  margin: 0;
  display: flex;
  flex-direction: column;
}
.place-photo img {
  width: 100%;
  height: 160px;
  object-fit: cover;
  border-radius: 6px;
  display: block;
}
.place-photo figcaption {
  font-size: 12px;
  color: var(--md-default-fg-color--light);
  font-style: italic;
  line-height: 1.4;
  margin-top: 6px;
}

/* Place page hero */
.place-hero {
  margin: 0 0 24px 0;
}
.place-hero img {
  width: 100%;
  max-height: 400px;
  object-fit: cover;
  border-radius: 8px;
  display: block;
}
.place-hero figcaption {
  font-size: 12px;
  color: var(--md-default-fg-color--light);
  font-style: italic;
  margin-top: 6px;
  text-align: center;
}

/* Place page footer block */
.place-footer {
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid var(--md-default-fg-color--lightest);
}
```

- [ ] **Step 3: Verify the existing extra.css is preserved**

```bash
head -20 site/docs/stylesheets/extra.css
```

If the file already had content, confirm it's still present above your new block. If not, the file should now contain only the new block.

### Task 6: Extend `on_post_page_macros` to render hero + footer for place pages

**Files:**
- Modify: `site/main.py`

- [ ] **Step 1: Update `on_post_page_macros` to handle place pages**

Replace the entire `on_post_page_macros(env)` function in `site/main.py` with:

```python
def on_post_page_macros(env):
    """Auto-append metadata bar and footers to project and place pages."""
    page = env.page
    src_path = page.file.src_path.replace("\\", "/")

    # Project pages (existing behaviour, with new related-places block)
    m = re.match(r"^(projects|completed|future)/(\d{3}-[^/]+)/index\.md$", src_path)
    if m:
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

        # Related places (new)
        places_field = meta.get("places", [])
        if isinstance(places_field, str):
            places_field = [places_field]
        places_block = ""
        if places_field:
            docs_dir = env.conf["docs_dir"]
            place_links = []
            for pid in places_field:
                place_file = Path(docs_dir) / "places" / f"{pid}.md"
                if place_file.exists():
                    pmeta, _ = _read_frontmatter(str(place_file))
                    ptitle = pmeta.get("title", pid)
                    place_links.append(f"[{ptitle}](../../places/{pid}.md)")
            if place_links:
                places_block = "\n\n**Places:** " + ", ".join(place_links)

        inspired = meta.get("inspired_by", "")
        inspired_line = ""
        if inspired:
            inspired_line = f"\n\n*Inspired by: {inspired}*"

        nav = "\n\n---\n\n*Questions or feedback? [Email us](mailto:info@tmbvillage.ie) at info@tmbvillage.ie.*\n"

        suffix = f"\n\n{meta_bar}{tags_block}{places_block}{inspired_line}{nav}"
        env.markdown += suffix
        return

    # Place pages (new)
    pm = re.match(r"^places/([a-z0-9_]+)\.md$", src_path)
    if pm:
        marker_id = pm.group(1)
        meta = page.meta
        category = meta.get("category", "")
        hero_file = meta.get("hero", "")
        docs_dir = env.conf["docs_dir"]

        # Hero (prepended at top of body)
        hero_block = ""
        if hero_file:
            # Look up the hero caption from _captions.json
            import json as _json
            captions_file = Path(docs_dir) / "assets" / "map-data" / "photos" / marker_id / "_captions.json"
            hero_caption = ""
            if captions_file.exists():
                try:
                    with open(captions_file, "r", encoding="utf-8") as f:
                        entries = _json.load(f)
                    for e in entries:
                        if e.get("file") == hero_file:
                            hero_caption = e.get("caption", "")
                            break
                except (_json.JSONDecodeError, OSError):
                    pass
            hero_block = (
                f'<figure class="place-hero">'
                f'<img src="../assets/map-data/photos/{marker_id}/{hero_file}" alt="{hero_caption}" />'
                f'<figcaption>{hero_caption}</figcaption>'
                f'</figure>\n\n'
            )

        # Find related projects (any project with this marker_id in its `places` field)
        related = []
        for subdir in ("projects", "future", "completed"):
            base = Path(docs_dir) / subdir
            if not base.exists():
                continue
            for proj_dir in sorted(base.iterdir()):
                if not proj_dir.is_dir():
                    continue
                idx = proj_dir / "index.md"
                if not idx.exists():
                    continue
                pmeta, _ = _read_frontmatter(str(idx))
                places_field = pmeta.get("places", [])
                if isinstance(places_field, str):
                    places_field = [places_field]
                if marker_id in places_field:
                    title = pmeta.get("title", proj_dir.name)
                    related.append(f"[{title}](../{subdir}/{proj_dir.name}/index.md)")

        related_block = ""
        if related:
            related_block = "\n\n**Related projects:** " + ", ".join(related)

        footer = (
            f'\n\n<div class="place-footer" markdown="1">\n\n'
            f"**Category:** {category}{related_block}\n\n"
            f"[← Show on the village map](../map.md)\n\n"
            f"</div>\n"
        )

        # Prepend hero to existing markdown, append footer
        env.markdown = hero_block + env.markdown + footer
        return
```

- [ ] **Step 2: Verify the build still passes**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -20
```

Expected: build succeeds. Place pages have their hero and footer rendered, but the body still says "[TODO: 2-4 paragraphs...]".

**Suggested commit point:** "add scaffold script, place_photos macro, and place page hooks" (Tasks 4-6 together).

---

### Task 7: Update `build_map.py` to inject `page_url` for markers with pages

**Files:**
- Modify: `scripts/build_map.py`

- [ ] **Step 1: Add page detection to the build script**

Modify `scripts/build_map.py`. After the `PHOTOS_DIR` line (around line 10), add:

```python
PLACES_DIR = ROOT / "site" / "docs" / "places"
```

Then, in the `build()` function, after the loop that calls `load_photos` for each marker, add a second loop that injects `page_url`:

```python
    for marker in markers:
        place_file = PLACES_DIR / f"{marker['id']}.md"
        if place_file.exists():
            marker["page_url"] = f"../places/{marker['id']}/"

    if bog_walk:
        bog_place = PLACES_DIR / "bog_walk.md"
        if bog_place.exists():
            bog_walk["page_url"] = "../places/bog_walk/"
```

The full modified `build()` function becomes (replace existing):

```python
def build():
    with open(MARKERS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    markers = data["markers"]
    bog_walk = data.get("bogWalk")

    for marker in markers:
        marker_photos = load_photos(marker["id"])
        marker["photos"] = marker_photos
        if marker_photos:
            print(f"  {marker['id']}: {len(marker_photos)} photo(s)")

        place_file = PLACES_DIR / f"{marker['id']}.md"
        if place_file.exists():
            marker["page_url"] = f"../places/{marker['id']}/"

    if bog_walk:
        bog_photos = load_photos("bog_walk")
        bog_walk["photos"] = bog_photos
        if bog_photos:
            print(f"  bog_walk: {len(bog_photos)} photo(s)")
        bog_place = PLACES_DIR / "bog_walk.md"
        if bog_place.exists():
            bog_walk["page_url"] = "../places/bog_walk/"

    build_data = json.dumps(
        {"markers": markers, "bogWalk": bog_walk},
        ensure_ascii=False,
        indent=None,
    )

    with open(TEMPLATE, "r", encoding="utf-8") as f:
        template = f.read()

    html = template.replace("/*{{MARKER_DATA}}*/", f"var MAP_DATA = {build_data};")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    photo_count = sum(len(m.get("photos", [])) for m in markers)
    bog_photo_count = len(bog_walk.get("photos", [])) if bog_walk else 0
    print(f"\nBuilt {OUTPUT}")
    print(f"  {len(markers)} markers, {photo_count} marker photos, {bog_photo_count} bog photos")
```

- [ ] **Step 2: Run build_map.py and verify page_url appears in output**

```bash
uv run python scripts/build_map.py
```

Then check the output:

```bash
grep -c "page_url" site/docs/assets/village-map.html
```

Expected: a positive count (one per place that has a page — should be 17).

### Task 8: Update map popup template to render "Read more →" button

**Files:**
- Modify: `site/docs/assets/map-template.html`

The existing `village-map.html` is generated. Find the source template — check whether `map-template.html` exists separately, and if not, use `village-map.html` as the template.

- [ ] **Step 1: Find the right file to edit**

```bash
ls site/docs/assets/map-template.html site/docs/assets/village-map.html 2>&1
```

If `map-template.html` exists, edit that. If not, the build process is regenerating `village-map.html` from a template — find it:

```bash
grep -l "MARKER_DATA" site/docs/assets/*.html scripts/*.py
```

Edit whichever file contains the `buildPopup` function and the placeholder `/*{{MARKER_DATA}}*/`.

- [ ] **Step 2: Add CSS for the read-more button**

Inside the `<style>` block in the template (near the existing `.popup-card .popup-links .gmaps-link` rule), add:

```css
.popup-card .popup-links .readmore-link {
    background: #e8f5e9;
    color: #2e7d32;
}
.popup-card .popup-links .readmore-link:hover {
    background: #c8e6c9;
}
```

- [ ] **Step 3: Update `buildPopup()` to render the read-more button**

In the `buildPopup` function, find the existing block that renders the popup-links (Google Maps button). It looks like this:

```javascript
'<div class="popup-links">' +
    '<a class="gmaps-link" href="' + gmapsUrl(...) + '" ...>Google Maps</a>' +
'</div>'
```

Replace that block with one that adds the read-more link when `m.page_url` exists:

```javascript
'<div class="popup-links">' +
    (m.page_url ? '<a class="readmore-link" href="' + m.page_url + '">Read more →</a>' : '') +
    '<a class="gmaps-link" href="' + gmapsUrl(coords[0], coords[1]) + '" target="_blank" rel="noopener">Open in Google Maps</a>' +
'</div>'
```

If the existing template uses different exact wording for the gmaps link, preserve that wording — only add the conditional `readmore-link` line.

- [ ] **Step 4: Rebuild the map and verify**

```bash
uv run python scripts/build_map.py
```

Then `cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs serve` and click any marker that has a page (e.g. the Monument). Confirm:
1. Popup shows "Read more →" button
2. Clicking it navigates to `/places/monument/`
3. Estate markers (e.g. Castle Park) show NO "Read more" button — only "Open in Google Maps"

**Suggested commit point:** "wire build_map.py and popup to link into places pages" (Tasks 7-8).

---

## Phase 2: Content — places that don't need research

For each content task: write 2-4 paragraphs replacing the `[TODO: ...]` placeholder in the scaffolded `.md` file. Voice rules from CLAUDE.md and memory:

- Casual, warm, committee voice. Hiberno-English allowed and encouraged.
- **No em-dashes.** Use commas, full stops, or parentheses.
- **No Latin names** for plants/birds.
- **No theatre metrics** (no fake litter weights, volunteer hours, FIT counts).
- **No competitor village names**, no "adjudicators praised X elsewhere" generics.
- Speak as the committee, not about the committee.

Source material per page: the existing `desc` in `markers.json`, the existing captions in `_captions.json`, plus relevant memory entries (e.g. `project_village_heritage.md` for blackcastle/liathmore, `project_pump_house_ev_charger.md`, `feedback_caption_style.md`, `feedback_no_competitor_names_public.md`).

After writing each cluster, run `cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build` to confirm no syntax errors, then visually check via `mkdocs serve`.

### Task 9: Cluster A — Heritage core (forge, seating_area, black_river)

These three are heritage / village features with rich photo material but minimal history beyond what's in captions.

**Files:**
- Modify: `site/docs/places/forge.md`
- Modify: `site/docs/places/seating_area.md`
- Modify: `site/docs/places/black_river.md`

- [ ] **Step 1: Write `forge.md`**

Open `site/docs/places/forge.md`. Keep the existing frontmatter and `{{ place_photos("forge") }}` line at the bottom. Replace the `[TODO: ...]` placeholder with 2-3 paragraphs covering:
- Position on the main street (beside Corcoran's parking)
- The iconic star above the archway, ivy on the gable, the cast-iron bench out front
- Restoration history (heritage feature, kept in good repair as part of the streetscape)
- Why it matters as a piece of village memory

- [ ] **Step 2: Write `seating_area.md`**

Cover:
- Where it is (western end of the village)
- What's there (bench seating, Box topiary, Laurel hedge, gravel path)
- The wildflower planting and what we get out of it (Alliums, Dandelion clocks, roses across the road)
- A line about it being a place to stop and look back into the village

- [ ] **Step 3: Write `black_river.md`**

Cover:
- The Black River as a tributary of the River Drish
- How it flows alongside Blackcastle and under the road
- The wildlife we see there (coots and ducks; willow and alder along the banks)
- A line connecting it to the wider water context (the river going on to the Drish, the wider catchment)

- [ ] **Step 4: Build and verify**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -10
```

Expected: build succeeds. Eyeball each page in the dev server.

### Task 10: Cluster B — Green spaces (sensory_garden, old_road_triangle)

Both have rich captions to draw from.

**Files:**
- Modify: `site/docs/places/sensory_garden.md`
- Modify: `site/docs/places/old_road_triangle.md`

- [ ] **Step 1: Write `sensory_garden.md`**

Cover:
- Location beside the school, link to school usage as outdoor classroom
- Built features (timber pergola, drystone amphitheatre, gravel paths, carved sculpture, willow dome)
- The sensory planting concept (Hawthorn, willow, grasses, scent and texture)
- Adjudicator note about path maintenance, current upkeep approach

- [ ] **Step 2: Write `old_road_triangle.md`**

Cover:
- The 2010 N75 reroute story (M8 Junction 5 opened, this wedge stranded between old and new alignment)
- The deliberate no-touch policy and why
- The bird list we hear in there in summer (Wren, Blackcap, Chiffchaff, Goldcrest, etc.)
- The Hazel coppice and Hawthorn arch
- Spanish vs native Bluebells, Stinging Nettle as butterfly host

This page is pure ecology/biodiversity. Lean into it.

- [ ] **Step 3: Build and verify**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -10
```

### Task 11: Cluster C — Businesses (bannons, tullys, corcorans, dempsey_motors)

Light, friendly. Pubs are pubs. Don't pad.

**Files:**
- Modify: `site/docs/places/bannons.md`
- Modify: `site/docs/places/tullys.md`
- Modify: `site/docs/places/corcorans.md`
- Modify: `site/docs/places/dempsey_motors.md`

- [ ] **Step 1: Write `bannons.md`**

1-2 paragraphs. Pub on the main street (L4202). Whatever current character notes are honest (a pub, the social heart, etc.). Don't fabricate specifics.

- [ ] **Step 2: Write `tullys.md`**

Same approach. Pub and shop on the main street. Note both functions.

- [ ] **Step 3: Write `corcorans.md`**

Bar with separate shop entrance. Note the planters out front and what the committee plants in them (split perennials from other beds, no annual buying).

- [ ] **Step 4: Write `dempsey_motors.md`**

Use memory entry `project_smj_refurb.md`-adjacent info: former Dempsey & Harold Motors garage, recently retired, redeveloped by Roadvacs (Irl) Limited as their new Tipperary base (offices and yard for liquid-waste-equipment business — NOT trucking). Frame as a positive Streetscape change. Reference memory `reference_roadvacs.md`.

- [ ] **Step 5: Build and verify**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -10
```

### Task 12: Cluster D — Centre features (monument, church, transport_museum)

`monument` has the 1900 hurling history (already on the plaque, mostly factual recital). `church` is light history. `transport_museum` is short.

**Files:**
- Modify: `site/docs/places/monument.md`
- Modify: `site/docs/places/church.md`
- Modify: `site/docs/places/transport_museum.md`

- [ ] **Step 1: Write `monument.md`**

This is one of the longer pages. Cover:
- Centre of the village, the All-Ireland Victory Centennial monument
- The 1900 final: TMB representing Tipperary, beat London 2-5 to 0-6 at Jones' Road
- The names plaque (don't enumerate all 35 names in prose — link to the photo for that)
- Unveiling: 26 August 2000 by Sean McCague (then GAA President), blessed by Most Rev. Dermot Clifford (Archbishop of Cashel and Emly), erected by Jerome Lennon for Stone Developments Ltd, Carlow
- The flower beds, sensory garden signpost, Christmas tree site
- The Mutt Mitt dispenser context (kept stocked, working with Cllr Sean Ryan on supply from Clonmel)
- Note: the bollard repaint sits in the projects tracker (which links here once Task 14 wires up the relationship)

- [ ] **Step 2: Write `church.md`**

Cover:
- St James, the calm centrepiece of the main street
- The bell-cote, three lancet windows
- The 2023 deep clean (Genie cherry-picker, Father Tom organising, committee chipping in)
- The bug hotel and what it's for
- Conversation underway about water butt at the cast-iron downpipe (link to project)
- Wildflower bed potential (adjudicator suggestion)

- [ ] **Step 3: Write `transport_museum.md`**

1-2 paragraphs. Car and transport museum. Currently temporarily closed. Use the photo material (gates dressed up for Vintage Coffee Morning, the planter scheme echoing across the village). Avoid making claims about reopening dates we don't know.

- [ ] **Step 4: Build and verify**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -10
```

### Task 13: Cluster E — Bog Walk

`bog_walk.md` has rich material to draw from.

**Files:**
- Modify: `site/docs/places/bog_walk.md`

- [ ] **Step 1: Write `bog_walk.md`**

Cover:
- The ~6.5km loop, where it starts (Clover entrance) and ends (back via Clover Lane off Ballyduff Road)
- The habitat mix: raised bog, dry heath, regenerating woodland
- Wildlife we see along it: Small Tortoiseshell butterfly, Common Darter dragonfly, Pale Tussock moth caterpillar, Red Squirrel (a real treat), Bog Cotton, Knapweed, Purple Loosestrife, Dog Rose, Bramble
- The annual St Bridget's Day Clover Bog Walk fundraiser, €1000 last year toward the village graveyard development
- The walk as a proper community fixture

- [ ] **Step 2: Build and verify**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -10
```

**Suggested commit point:** "write content for non-research places" (Tasks 9-13 together: forge, seating_area, black_river, sensory_garden, old_road_triangle, bannons, tullys, corcorans, dempsey_motors, monument, church, transport_museum, bog_walk).

---

## Phase 3: Content — places needing research

Each task here begins with web research, then prose. Flag any uncertain claim with an inline `<!-- TODO: verify -->` HTML comment so the user can spot-check before publishing. Do NOT invent facts.

### Task 14: blackcastle (with research)

**Files:**
- Modify: `site/docs/places/blackcastle.md`

- [ ] **Step 1: Research the castle**

Search the web for:
- "Blackcastle Two Mile Borris Tipperary"
- "Two Mile Borris tower house"
- NIAH (Buildings of Ireland) entry for Two Mile Borris
- Wikipedia article if any

Resolve in particular:
- Is it 12th-century or 16th-century? (The current site has both claims.)
- Is it correctly classified as a Norman tower house, an Anglo-Norman tower house, or a later tower house?
- Any known builders / owners of record?
- Is there a National Monument number?

Note any authoritative sources (NIAH reference, Heritage Council, Tipperary heritage register).

- [ ] **Step 2: Write `blackcastle.md`**

Cover:
- Where it is (western edge of the village, beside the Black River)
- The dating answer from research, with confidence level (e.g. "around the 14th–16th century" if sources differ; cite the NIAH date if that's authoritative)
- Building description (four storeys, corner turret, medieval stonework)
- The cottage out front giving scale
- The unmown meadow at the back, Hawthorn blossom, biodiversity narrative connecting castle and current ecology

If research uncovers inconsistency with existing captions (e.g. dating), update `_captions.json` for `blackcastle/` to match the authoritative dating. Inline `<!-- TODO: verify -->` for any remaining uncertain claim.

- [ ] **Step 3: Update markers.json desc to match**

Edit the `blackcastle` entry's `desc` in `site/docs/assets/map-data/markers.json` to a 1-line teaser (the page carries the detail now). Example:

```
"desc": "Norman tower house on the western edge of the village, with the Black River running past."
```

- [ ] **Step 4: Build and verify**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -10
uv run python scripts/build_map.py
```

### Task 15: liathmore (with research)

**Files:**
- Modify: `site/docs/places/liathmore.md`

- [ ] **Step 1: Research the monastic site**

Search:
- "Liathmore monastic site Tipperary"
- "St Mochoemog Liathmore"
- "Liathmore sheela-na-gig"
- archaeology.ie for any state-protected status
- megalithicireland.com

Resolve:
- Founding date (the current text says 7th century — confirm)
- Mochoemog's dates and death year if known
- Date of the larger 12th-century church (current text says 12th century)
- Confirmed presence of: Romanesque doorway, sheela-na-gig, round tower foundation
- Any National Monument number

- [ ] **Step 2: Write `liathmore.md`**

Cover:
- 2.8km east of the village
- Founding by St Mochoemog (give dates if research yields them), and that our village school Scoil Mochaomhóg Naofa NS is named after him — that connection is one of the loveliest things about the site
- Two ruined churches and the round tower foundation
- The 12th-century Romanesque doorway on the larger church
- The sheela-na-gig carving (small, weathered, in the doorway — from photo it's tucked in, photo credit A.-K. D. via Wikimedia CC-BY-SA 4.0)
- Why we count it as ours (within the parish, gives the school its name, sits in our broader heritage map)

Inline `<!-- TODO: verify -->` for anything not nailed down.

- [ ] **Step 3: Update markers.json desc to a 1-line teaser**

```
"desc": "Seventh-century monastic site about 2.8km east of the village, founded by the saint who gave our school its name."
```

- [ ] **Step 4: Build and verify**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -10
uv run python scripts/build_map.py
```

### Task 16: school (with research)

**Files:**
- Modify: `site/docs/places/school.md`

- [ ] **Step 1: Research the school**

The cast plaque on the wall already says "Two mile Borris National School March 1846" (visible in the heritage plaque photo). Search for:
- "Scoil Mochaomhóg Naofa Two Mile Borris"
- The school's website (if any) for principal/staff list, current enrolment, Green Schools status
- Department of Education historical records if accessible

Confirm:
- 1846 founding (cast plaque is authoritative)
- Continuous operation since
- Current name change to Scoil Mochaomhóg Naofa NS (when did this happen?)
- Green Schools programme details

- [ ] **Step 2: Write `school.md`**

Cover:
- Founded 1846 (the year before the Famine started — anchor that line)
- Continuous community education on the same site for nearly 180 years
- The original 1846 cast plaque embedded in the wall (anchor as the heritage feature)
- The newer Áras Montessori extension on the left vs original schoolhouse on the right
- Naming: Scoil Mochaomhóg Naofa NS, named after the same saint who founded Liathmore (link the two pages)
- The Green Schools programme, the sensory garden right beside it (link to that page)
- Adjudicator note: elaborate the connection to Green Schools in the application

`<!-- TODO: verify -->` for current enrolment numbers, principal name, exact Green Schools flag count if claimed — only include if the school confirms.

- [ ] **Step 3: Update markers.json desc**

```
"desc": "Our village national school, on the same site since 1846. Green Schools programme, Áras Montessori extension."
```

- [ ] **Step 4: Build and verify**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -10
uv run python scripts/build_map.py
```

### Task 17: cemetery (with research)

**Files:**
- Modify: `site/docs/places/cemetery.md`

- [ ] **Step 1: Research the cemetery**

Search:
- "Two Mile Borris cemetery Tipperary"
- "Two Mile Borris graveyard history"
- Tipperary County Council burial records
- Historic Graves Project (historicgraves.com)
- The Bog Walk fundraiser cheque presentation 2025 (€1000 toward graveyard development) — already in memory

Confirm:
- When the cemetery was consecrated / first burials
- Notable burials if any (avoid sensitive personal details)
- Date the new extension opened (the construction photo is from spring 2025; new entrance pillars and gravel sweep visible in May 2026 photo)

- [ ] **Step 2: Write `cemetery.md`**

Note: this page absorbs the `new_cemetery_entrance` content (no separate page). Cover:
- Position (west end of the village, beside Blackcastle)
- The original gates with carved stone urn finials, framed by the old Cypress
- The two committee blue trough planters at the layby (locally made, part of the cohesive village planter scheme)
- The new entrance on the L4202: stone pillars, dedication plaque, gravel sweep
- The 2025 graveyard extension (info board, layout, spring 2025 construction)
- The St Bridget's Day Clover Bog Walk fundraiser link — €1000 went to graveyard development
- The biodiversity-rich landscaping opportunity flagged by the adjudicator (link to project 019)

`<!-- TODO: verify -->` consecration date if the research turned anything up.

- [ ] **Step 3: Update markers.json — fold new_cemetery_entrance into cemetery teaser**

Update the `cemetery` desc to a 1-line teaser:

```
"desc": "The village cemetery on the western edge, with original gates and a 2025 extension."
```

Leave `new_cemetery_entrance` in markers.json as-is (still a useful pin on the map, but no page — its photos and content live on the cemetery page now).

- [ ] **Step 4: Build and verify**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build 2>&1 | tail -10
uv run python scripts/build_map.py
```

**Suggested commit point:** "write research-led content for blackcastle, liathmore, school, cemetery" (Tasks 14-17 together).

---

## Phase 4: Project ↔ place linking

### Task 18: Add `places:` frontmatter to project files

**Files:**
- Modify: every relevant project file under `site/docs/projects/*/index.md`, `site/docs/future/*/index.md`, `site/docs/completed/*/index.md`

- [ ] **Step 1: List all projects and identify their places**

```bash
ls site/docs/projects/ site/docs/future/ site/docs/completed/ 2>/dev/null
```

For each project folder, read the `index.md` and decide which place(s) it relates to. Mapping (build this table by reading each project file's content):

| Project | Places to link |
|---------|----------------|
| 010-water-butts | church |
| 013-repaint-bollards | monument |
| 016-glen-carraig-wildflower | (no place page — estate) |
| 017-noel-hayes-park-bedding | (no place page — estate) |
| 019-graveyard-biodiversity-landscaping | cemetery |
| ... | ... |

Skip any project whose target is an estate or an approach road (no place page exists for those).

- [ ] **Step 2: Add `places:` field to each relevant project file**

Open each project's `index.md` and add a `places:` list to the frontmatter. Example for `site/docs/projects/010-water-butts/index.md`:

```yaml
---
title: "Install water butts for watering containers and baskets"
delivery_year: 2026
tags:
  - sustainability
status: "In progress, finalising location (May 2026)"
cost_estimate: "€100-150"
benefit: "Medium"
volunteer_hours: "4hrs (installation)"
inspired_by: "2025 adjudication recommendation"
special_award: "Sustainability & Circular Economy"
places:
  - church
---
```

- [ ] **Step 3: Build and verify cross-links render in both directions**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs serve
```

Open in browser:
1. `/projects/010-water-butts/` — confirm "**Places:** [St James Church]" line appears below the metadata bar
2. `/places/church/` — confirm "**Related projects:** [Install water butts...]" line appears in the footer
3. Repeat spot-check for 2-3 other project/place pairs

- [ ] **Step 4: Commit**

Suggested commit: "wire project ↔ place cross-references via places frontmatter"

---

## Phase 5: Polish

### Task 19: Shorten remaining `desc` fields in `markers.json`

**Files:**
- Modify: `site/docs/assets/map-data/markers.json`

For markers that have a page but whose `desc` is still verbose (because not updated in tasks 14-17), shorten to a 1-line teaser. Affects at least:

- `monument` (currently very long with the 1900 history — page carries that now)
- `old_road_triangle` (long ecology paragraph — page carries that now)
- `liathmore` (already updated in Task 15)
- `blackcastle` (already updated in Task 14)
- `cemetery` (already updated in Task 17)
- `school` (already updated in Task 16)

- [ ] **Step 1: Update each verbose desc**

Replace the `desc` for `monument`:

```json
"desc": "The heart of the village. Anchored by our All-Ireland Victory Centennial monument, marking the 1900 hurling final."
```

Replace the `desc` for `old_road_triangle`:

```json
"desc": "Wedge of mature trees stranded between the old and new N75 alignments. Wildlife refuge inside the village edge."
```

Walk through every other place marker and tighten any `desc` longer than ~150 chars.

- [ ] **Step 2: Rebuild map**

```bash
uv run python scripts/build_map.py
```

- [ ] **Step 3: Verify in browser**

Open the map page in the dev server. Click each place marker. Confirm:
1. Popup desc is short and inviting
2. "Read more →" button leads to the full page
3. No place's popup feels truncated awkwardly

### Task 20: Final walkthrough

- [ ] **Step 1: Walk every page in dev server**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs serve
```

Visit in order:
1. `/` (home — nav reflects Future-under-Projects)
2. `/places/` (gateway, all 17 places listed under categories)
3. `/places/blackcastle/` through `/places/bog_walk/` — every page in turn
4. `/map/` — every place marker click → "Read more" → back via "← Show on map"
5. 2-3 project pages with `places:` frontmatter → confirm "Places:" line shows

- [ ] **Step 2: Build with --strict and confirm no warnings**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs build --strict 2>&1 | tail -20
```

Expected: zero warnings, zero errors.

- [ ] **Step 3: Final commit**

Suggested commit: "polish: tighten marker descs, walk-through verified"

---

## Self-review notes

Before handing off:

- Spec coverage: nav change ✓ (T1), `places/` structure ✓ (T4), template + macros ✓ (T3, T5, T6), map popup ✓ (T7-T8), project ↔ place linking ✓ (T18), 17 prose pages ✓ (T9-T17), out-of-scope items not implemented ✓.
- Placeholders in plan: none beyond intentional content placeholders that the prose tasks fill.
- Type/path consistency: all paths checked (`places/{id}.md` flat, `../places/{id}/` URL from map iframe, `marker_id` field consistently in both directions).
- One known judgement call: in Task 18, the project ↔ place mapping table is sketched but the engineer must read each project file to fill it in fully. That's deliberate — the source of truth is what's actually written in each project's prose.
