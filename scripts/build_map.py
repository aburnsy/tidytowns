"""Build the village map HTML from markers.json, photo folders, and template."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "site" / "docs" / "assets"
MAP_DATA = ASSETS / "map-data"
MARKERS_JSON = MAP_DATA / "markers.json"
PHOTOS_DIR = MAP_DATA / "photos"
TEMPLATE = ASSETS / "map-template.html"
OUTPUT = ASSETS / "village-map.html"


def load_photos(marker_id: str) -> list[dict]:
    folder = PHOTOS_DIR / marker_id
    if not folder.is_dir():
        return []

    captions_file = folder / "_captions.json"
    if not captions_file.exists():
        return []

    with open(captions_file, "r", encoding="utf-8") as f:
        entries = json.load(f)

    photos = []
    for entry in entries:
        img_path = folder / entry["file"]
        if img_path.exists():
            rel_path = img_path.relative_to(ASSETS).as_posix()
            photos.append({"src": rel_path, "caption": entry["caption"]})
        else:
            print(f"  Warning: {img_path} not found, skipping")
    return photos


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

    if bog_walk:
        bog_photos = load_photos("bog_walk")
        bog_walk["photos"] = bog_photos
        if bog_photos:
            print(f"  bog_walk: {len(bog_photos)} photo(s)")

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
    print(f"  {len(markers)} markers, {photo_count} marker photos, {bog_photo_count} bog walk photos")


if __name__ == "__main__":
    build()
