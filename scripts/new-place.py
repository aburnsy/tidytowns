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

    fm_lines = [
        "---",
        f'title: "{title}"',
        f"marker_id: {marker_id}",
        f'category: "{category}"',
    ]
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
