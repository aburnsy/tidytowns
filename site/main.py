"""mkdocs-macros hook for TMB Tidy Towns project tracker.

Provides:
- on_post_page_macros hook: auto-renders project metadata bar and place page hero/footer
- project_list_by_year() macro: grouped active project listing
- completed_project_list() macro: grouped completed project listing
- place_list_by_category() macro: places gateway, grouped by category
- place_photos() macro: photo gallery for a place page
"""

import datetime
import json
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


def _load_markers(docs_dir):
    """Load markers.json and return {marker_id: marker_dict}."""
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
    def place_list_by_category():
        """Render places grouped by category as cards/links."""
        docs_dir = env.conf["docs_dir"]
        places = _scan_places(docs_dir)
        markers = _load_markers(docs_dir)

        src_path = env.page.file.src_path.replace("\\", "/")
        prefix = "" if src_path.startswith("places/") else "places/"

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
                if len(teaser) > 140:
                    teaser = teaser[:137].rsplit(" ", 1)[0] + "…"
                if teaser:
                    lines.append(f"- **[{title}]({prefix}{fname}.md)** — {teaser}")
                else:
                    lines.append(f"- **[{title}]({prefix}{fname}.md)**")
            lines.append("")
        return "\n".join(lines)

    @env.macro
    def place_photos(*marker_ids, limit=None):
        """Render a photo grid pulling from one or more photo folders.

        The first photo of the FIRST folder is skipped (it's the hero, already
        rendered above the prose). All photos from subsequent folders are
        included. Photos link to the full-size image. Pages can pass `limit`
        to cap count.
        """
        if not marker_ids:
            return ""

        docs_dir = env.conf["docs_dir"]
        src_path = env.page.file.src_path.replace("\\", "/")
        prefix = "../../" if src_path.startswith("places/") else ""

        # Collect (folder, entry) pairs across all requested folders
        all_entries = []
        for idx, marker_id in enumerate(marker_ids):
            captions_file = (
                Path(docs_dir) / "assets" / "map-data" / "photos" / marker_id / "_captions.json"
            )
            if not captions_file.exists():
                continue
            try:
                with open(captions_file, "r", encoding="utf-8") as f:
                    entries = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
            if not entries:
                continue
            # Skip the hero on the FIRST folder only
            if idx == 0:
                entries = entries[1:]
            for e in entries:
                all_entries.append((marker_id, e))

        if limit is not None:
            all_entries = all_entries[:limit]
        if not all_entries:
            return ""

        items = ['<div class="place-gallery" markdown="0">']
        for marker_id, entry in all_entries:
            file = entry.get("file", "")
            caption = entry.get("caption", "")
            if not file:
                continue
            alt = caption.replace('"', "&quot;")
            photo_base = f"{prefix}assets/map-data/photos/{marker_id}"
            items.append(
                f'<figure class="place-photo">'
                f'<a href="{photo_base}/{file}" target="_blank" rel="noopener">'
                f'<img src="{photo_base}/{file}" alt="{alt}" loading="lazy" />'
                f"</a>"
                f"<figcaption>{caption}</figcaption>"
                f"</figure>"
            )
        items.append("</div>")
        return "\n".join(items)

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
    """Auto-append metadata bar / hero / footer to project and place pages."""
    page = env.page
    src_path = page.file.src_path.replace("\\", "/")

    # Project page (active, future, or completed)
    m = re.match(r"^(projects|completed|future)/(\d{3}-[^/]+)/index\.md$", src_path)
    if m:
        meta = page.meta
        docs_dir = env.conf["docs_dir"]

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

        # Related places (new): list of marker_ids in `places:` frontmatter
        places_field = meta.get("places", [])
        if isinstance(places_field, str):
            places_field = [places_field]
        places_block = ""
        if places_field:
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

    # Place page
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
            captions_file = (
                Path(docs_dir) / "assets" / "map-data" / "photos" / marker_id / "_captions.json"
            )
            hero_caption = ""
            if captions_file.exists():
                try:
                    with open(captions_file, "r", encoding="utf-8") as f:
                        entries = json.load(f)
                    for e in entries:
                        if e.get("file") == hero_file:
                            hero_caption = e.get("caption", "")
                            break
                except (json.JSONDecodeError, OSError):
                    pass
            alt = hero_caption.replace('"', "&quot;")
            hero_block = (
                f'<figure class="place-hero">'
                f'<img src="../../assets/map-data/photos/{marker_id}/{hero_file}" alt="{alt}" />'
                f"<figcaption>{hero_caption}</figcaption>"
                f"</figure>\n\n"
            )

        # Related projects: scan projects/, future/, completed/ for any
        # whose `places:` frontmatter contains this marker_id
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

        env.markdown = hero_block + env.markdown + footer
        return
