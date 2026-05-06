# Bog Walk Map Feature — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the bog walk from a minimal dashed polyline with two entrance markers to a central interactive map feature — one clickable path with glow styling, photo gallery popup, and interactive legend.

**Architecture:** Replace `bogWalkPath` array and two entrance markers with a single `bogWalk` object in markers.json. The build script attaches photos from a `bog_walk/` folder. The template renders dual stacked polylines (glow + main), binds a popup using the existing card pattern, and makes all legend rows clickable (bog walk zooms/pulses, others toggle category visibility).

**Tech Stack:** Leaflet.js (already in use), vanilla JS, Python build script (`build_map.py`)

**Spec:** `docs/superpowers/specs/2026-05-06-bog-walk-map-feature-design.md`

---

### Task 1: Move photos and restructure data

Move bog_entrance_1 photos to a new bog_walk folder, remove the two entrance markers from markers.json, and replace `bogWalkPath` with the `bogWalk` object.

**Files:**
- Create: `site/docs/assets/map-data/photos/bog_walk/_captions.json`
- Move: `site/docs/assets/map-data/photos/bog_entrance_1/*.jpg` → `site/docs/assets/map-data/photos/bog_walk/`
- Delete: `site/docs/assets/map-data/photos/bog_entrance_1/` (entire folder)
- Delete: `site/docs/assets/map-data/photos/bog_entrance_2/` (entire folder — only has empty `_captions.json`)
- Modify: `site/docs/assets/map-data/markers.json`

- [ ] **Step 1: Create bog_walk photo folder and move photos**

```bash
mkdir -p site/docs/assets/map-data/photos/bog_walk
cp site/docs/assets/map-data/photos/bog_entrance_1/*.jpg site/docs/assets/map-data/photos/bog_walk/
```

- [ ] **Step 2: Create _captions.json for bog_walk**

Write `site/docs/assets/map-data/photos/bog_walk/_captions.json`:

```json
[
  {
    "file": "knapweed-butterfly-summer-2025.jpg",
    "caption": "Small Tortoiseshell butterfly on Knapweed, with Yarrow in the background"
  },
  {
    "file": "tortoiseshell-closeup-summer-2025.jpg",
    "caption": "Small Tortoiseshell butterfly resting on Knapweed along The Bog Walk"
  },
  {
    "file": "bog-walk-wildflowers-summer-2025.jpg",
    "caption": "Knapweed, Hogweed and native meadow grasses along The Bog Walk"
  }
]
```

- [ ] **Step 3: Delete old entrance photo folders**

```bash
rm -rf site/docs/assets/map-data/photos/bog_entrance_1
rm -rf site/docs/assets/map-data/photos/bog_entrance_2
```

- [ ] **Step 4: Update markers.json**

Remove the two entrance marker objects (ids `bog_entrance_1` and `bog_entrance_2`) from the `markers` array.

Replace the top-level `"bogWalkPath"` key with `"bogWalk"`:

```json
"bogWalk": {
  "name": "Bog Walk Loop",
  "description": "A looped walk through bogland starting from the Clover entrance, heading north through open bog, and returning via Clover Lane off the Ballyduff Road.",
  "distance": "~2.5 km loop",
  "category": "Bog Walk",
  "color": "#1B5E20",
  "path": [
    [52.672271, -7.696315],
    [52.6730, -7.6958],
    [52.6742, -7.6950],
    [52.6758, -7.6948],
    [52.6775, -7.6955],
    [52.6790, -7.6975],
    [52.6800, -7.7005],
    [52.6810, -7.7040],
    [52.6818, -7.7065],
    [52.682152, -7.709246]
  ]
}
```

Note: The path coordinates are the same 10-point placeholder. They will be replaced with real traced coordinates in a later step (user to provide).

- [ ] **Step 5: Verify JSON is valid**

```bash
uv run python -c "import json; json.load(open('site/docs/assets/map-data/markers.json')); print('OK')"
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add site/docs/assets/map-data/
git commit -m "data: restructure bog walk as unified feature, move photos to bog_walk/"
```

---

### Task 2: Update build script

Update `build_map.py` to read the new `bogWalk` object, attach photos, and inject it into MAP_DATA.

**Files:**
- Modify: `scripts/build_map.py`

- [ ] **Step 1: Update the build function**

Replace the entire `build()` function in `scripts/build_map.py` with:

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
```

- [ ] **Step 2: Run the build to verify**

```bash
uv run python scripts/build_map.py
```

Expected output includes:
```
  bog_walk: 3 photo(s)
  ...
  26 markers, NN marker photos, 3 bog walk photos
```

(26 markers — down from 28 after removing the two entrance markers.)

- [ ] **Step 3: Commit**

```bash
git add scripts/build_map.py
git commit -m "build: update build_map.py to handle unified bogWalk object"
```

---

### Task 3: Template — dual polyline with popup

Replace the single dashed polyline with a glow + main polyline, add hover effect, and bind a popup using the existing card pattern.

**Files:**
- Modify: `site/docs/assets/map-template.html`

- [ ] **Step 1: Add distance support to buildPopup**

In `site/docs/assets/map-template.html`, find the `buildPopup` function. Locate this line inside it:

```javascript
'<p>' + m.desc + '</p>' +
```

Replace with:

```javascript
(m.distance ? '<p style="margin:0 0 8px 0;font-size:13px;color:#1B5E20;font-weight:600;">' + m.distance + '</p>' : '') +
'<p>' + m.desc + '</p>' +
```

- [ ] **Step 2: Replace the bog walk polyline rendering**

Find this block (lines 183-188):

```javascript
// Bog walk trail
if (MAP_DATA.bogWalkPath && MAP_DATA.bogWalkPath.length > 1) {
    L.polyline(MAP_DATA.bogWalkPath, {
        color: '#1B5E20', weight: 4, opacity: 0.8,
        dashArray: '10', interactive: false
    }).addTo(map);
}
```

Replace with:

```javascript
// Bog walk trail — dual polyline (glow + main) with popup
var bogGlow, bogPath, bogMidpoint;
var bogWalk = MAP_DATA.bogWalk;
if (bogWalk && bogWalk.path && bogWalk.path.length > 1) {
    bogGlow = L.polyline(bogWalk.path, {
        color: bogWalk.color, weight: 12, opacity: 0.3,
        interactive: false
    }).addTo(map);

    bogPath = L.polyline(bogWalk.path, {
        color: '#2E7D32', weight: 5, opacity: 0.9,
        lineCap: 'round', lineJoin: 'round'
    }).addTo(map);

    bogPath.on('mouseover', function() {
        this.setStyle({ weight: 7 });
        this.getElement().style.cursor = 'pointer';
    });
    bogPath.on('mouseout', function() {
        this.setStyle({ weight: 5 });
    });

    var midIdx = Math.floor(bogWalk.path.length / 2);
    bogMidpoint = bogWalk.path[midIdx];

    photosByName[bogWalk.name] = bogWalk.photos || [];

    var bogMarkerData = {
        name: bogWalk.name,
        category: bogWalk.category,
        color: bogWalk.color,
        desc: bogWalk.description,
        distance: bogWalk.distance,
        coords: bogMidpoint,
        photos: bogWalk.photos || []
    };
    bogPath.bindPopup(buildPopup(bogMarkerData), { maxWidth: 320, minWidth: 280 });
}
```

- [ ] **Step 3: Rebuild and verify**

```bash
uv run python scripts/build_map.py
```

Then preview the site:

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs serve
```

Verify:
- Bog walk path shows as solid green line with a wider glow underneath
- Hovering the path thickens it and shows pointer cursor
- Clicking the path opens a popup with title, distance, description, and 3 photos
- Photo thumbnails open the lightbox carousel
- No more entrance marker pins on the map

- [ ] **Step 4: Commit**

```bash
git add site/docs/assets/map-template.html
git commit -m "feat: dual polyline bog walk with glow styling and popup"
```

---

### Task 4: Template — interactive legend

Make all legend rows clickable. Bog Walk row zooms to path and opens popup. Other category rows toggle marker visibility.

**Files:**
- Modify: `site/docs/assets/map-template.html`

- [ ] **Step 1: Update legend HTML**

Find the legend div and replace it entirely:

```html
<div id="legend">
    <b>Legend</b>
    <div class="legend-row" data-category="Village Features"><span class="legend-dot" style="background:#2196F3"></span> Village Features</div>
    <div class="legend-row" data-category="Businesses"><span class="legend-dot" style="background:#FF9800"></span> Businesses</div>
    <div class="legend-row" data-category="Green Spaces &amp; Nature"><span class="legend-dot" style="background:#4CAF50"></span> Green Spaces &amp; Nature</div>
    <div class="legend-row legend-featured" data-category="Bog Walk"><span class="legend-line" style="border-color:#2E7D32"></span> <strong>Bog Walk Loop</strong></div>
    <div class="legend-row" data-category="School"><span class="legend-dot" style="background:#9C27B0"></span> School</div>
    <div class="legend-row" data-category="Housing Estates"><span class="legend-dot" style="background:#00838F"></span> Housing Estates</div>
    <div class="legend-row" data-category="Other"><span class="legend-dot" style="background:#37474F"></span> Other</div>
    <div class="legend-row" data-category="Approach Roads"><span class="legend-dot" style="background:#F44336"></span> Approach Roads</div>
</div>
```

Changes from current: removed "Points of Interest" row (no markers use it), removed separate "Bog Walk Trail" line row, combined into single "Bog Walk Loop" featured row, added `data-category` to all rows.

- [ ] **Step 2: Add legend-row CSS**

In the `<style>` block, after the existing `.legend-line` rule, add:

```css
.legend-row { cursor: pointer; padding: 2px 4px; border-radius: 4px; transition: opacity 0.2s, background 0.2s; }
.legend-row:hover { background: rgba(0,0,0,0.05); }
.legend-row.dimmed { opacity: 0.4; }
.legend-featured { background: rgba(27,94,32,0.08); }
```

- [ ] **Step 3: Restructure marker creation to use category LayerGroups**

Find the `MAP_DATA.markers.forEach` block:

```javascript
MAP_DATA.markers.forEach(function(m) {
    photosByName[m.name] = m.photos || [];
    var popup = buildPopup(m);
    var marker = L.marker(m.coords, { icon: createIcon(m.color) }).addTo(map);
    marker.bindPopup(popup, { maxWidth: 320, minWidth: 280 });
    marker.bindTooltip(m.name, { permanent: false, direction: 'top', offset: [0, -42] });
});
```

Replace with:

```javascript
var categoryLayers = {};

MAP_DATA.markers.forEach(function(m) {
    photosByName[m.name] = m.photos || [];
    var popup = buildPopup(m);
    var marker = L.marker(m.coords, { icon: createIcon(m.color) });
    marker.bindPopup(popup, { maxWidth: 320, minWidth: 280 });
    marker.bindTooltip(m.name, { permanent: false, direction: 'top', offset: [0, -42] });

    if (!categoryLayers[m.category]) {
        categoryLayers[m.category] = L.layerGroup().addTo(map);
    }
    categoryLayers[m.category].addLayer(marker);
});
```

- [ ] **Step 4: Add legend click handlers**

After the `MAP_DATA.markers.forEach` block (and after the bog walk polyline code), add:

```javascript
// Legend interactivity
document.querySelectorAll('.legend-row[data-category]').forEach(function(row) {
    row.addEventListener('click', function() {
        var cat = this.getAttribute('data-category');

        if (cat === 'Bog Walk') {
            if (bogPath) {
                map.fitBounds(bogPath.getBounds(), { padding: [50, 50] });
                if (bogGlow) {
                    bogGlow.setStyle({ opacity: 0.6 });
                    setTimeout(function() { bogGlow.setStyle({ opacity: 0.3 }); }, 600);
                }
                bogPath.openPopup(L.latLng(bogMidpoint[0], bogMidpoint[1]));
            }
            return;
        }

        var layer = categoryLayers[cat];
        if (!layer) return;

        if (map.hasLayer(layer)) {
            map.removeLayer(layer);
            this.classList.add('dimmed');
        } else {
            layer.addTo(map);
            this.classList.remove('dimmed');
        }
    });
});
```

- [ ] **Step 5: Rebuild and verify**

```bash
uv run python scripts/build_map.py
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs serve
```

Verify:
- All legend rows show pointer cursor on hover
- Clicking "Bog Walk Loop" zooms to the path, glow pulses brighter briefly, popup opens
- Clicking other categories (e.g. "Housing Estates") hides those markers; the legend row dims
- Clicking the dimmed row again restores the markers
- The "Bog Walk Loop" row has a subtle green background highlight

- [ ] **Step 6: Commit**

```bash
git add site/docs/assets/map-template.html
git commit -m "feat: interactive legend with category toggle and bog walk zoom"
```

---

### Task 5: Final build and cleanup

Run the full build, verify everything works end-to-end, clean up.

**Files:** None new — verification only.

- [ ] **Step 1: Full rebuild**

```bash
uv run python scripts/build_map.py
```

- [ ] **Step 2: Preview and verify all features**

```bash
cd site && uv run --with mkdocs-material --with mkdocs-macros-plugin mkdocs serve
```

Checklist:
- [ ] Bog walk shows as solid green line with glow
- [ ] Hovering the path thickens it
- [ ] Clicking the path opens popup with title, distance, description, 3 photos
- [ ] Photo gallery opens lightbox carousel
- [ ] Legend "Bog Walk Loop" click zooms to path, pulses glow, opens popup
- [ ] Legend category clicks toggle markers on/off with dimming
- [ ] No entrance marker pins visible
- [ ] All other markers still work (click, popup, photos)
- [ ] Satellite and street map layers still work

- [ ] **Step 3: Commit any final adjustments and verify git status is clean**

```bash
git status
```
