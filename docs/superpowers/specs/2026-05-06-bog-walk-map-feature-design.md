# Bog Walk Map Feature — Design Spec

## Summary

Upgrade the bog walk from a minimal dashed polyline with two entrance markers to a central interactive feature on the village map. The walk becomes a single unified entity — one clickable path with a photo gallery popup, prominent glow styling, and interactive legend integration.

## Current State

- 10-point dashed polyline (`weight: 4, dashArray: '10', interactive: false`)
- Two separate entrance markers (`bog_entrance_1`, `bog_entrance_2`) in the "Bog Walk" category
- Static legend with no click handlers
- Photos only on `bog_entrance_1`
- Path coordinates are a rough approximation, not the real route

## Design

### Data Model (markers.json)

Remove `bog_entrance_1` and `bog_entrance_2` from the `markers` array. Replace the top-level `bogWalkPath` array with a `bogWalk` object:

```json
{
  "markers": [ ... ],
  "bogWalk": {
    "name": "Bog Walk Loop",
    "description": "A looped walk through bogland starting from the Clover entrance, heading north through open bog, and returning via Clover Lane off the Ballyduff Road.",
    "distance": "~2.5 km",
    "category": "Bog Walk",
    "color": "#1B5E20",
    "path": [ [lat, lng], ... ]
  }
}
```

The `path` array will be replaced with real traced coordinates (user to provide). The distance value will be updated once the real path length is known.

Photos go in `site/docs/assets/map-data/photos/bog_walk/` with `_captions.json`, same convention as other markers. Existing photos from `bog_entrance_1/` will be moved to `bog_walk/`.

### Visual Styling (map-template.html)

Two stacked Leaflet polylines replace the current single dashed line:

- **Glow layer** (underneath): `weight: 12, color: '#1B5E20', opacity: 0.3` — wide semi-transparent halo. Not interactive.
- **Main path** (on top): `weight: 5, color: '#2E7D32', opacity: 0.9, lineCap: 'round', lineJoin: 'round'` — solid bright green line. Interactive (clickable).

Hover effect on main path: `weight: 7`, cursor changes to pointer.

### Legend Interactivity

All legend rows become clickable:

- **Bog Walk row**: Zooms map to fit the path bounds (with padding), briefly pulses the glow layer opacity (0.3 -> 0.6 -> 0.3 over ~600ms), and opens the popup at the path midpoint. Row has subtle bold/highlight treatment to signal it's the featured item.
- **Other category rows**: Toggle that category's markers on/off. The legend row itself dims (reduced opacity) when its category is hidden.

### Popup

Click the path or the legend row -> popup opens at the path midpoint. Uses the same popup card pattern as existing markers:

- Hero photo (first from `bog_walk/` gallery)
- Photo caption
- "Bog Walk Loop" title
- Category badge (color: #1B5E20)
- Distance line (e.g. "~2.5 km loop")
- Description text
- Thumbnail gallery -> opens existing lightbox carousel
- Google Maps link (centred on path midpoint)

### Build Script (build_map.py)

Updated to:

- Read `bogWalk` object from markers.json (instead of `bogWalkPath`)
- Call `load_photos("bog_walk")` and attach result to bogWalk data
- Inject `{"markers": [...], "bogWalk": {...}}` into MAP_DATA
- Print bog walk photo count in build output

### Files Changed

1. `site/docs/assets/map-data/markers.json` — restructure bogWalkPath to bogWalk object, remove entrance markers
2. `scripts/build_map.py` — handle bogWalk object and its photos
3. `site/docs/assets/map-template.html` — dual polyline, interactive legend, path popup, hover effects
4. `site/docs/assets/map-data/photos/bog_walk/` — photo folder (move existing entrance photos)

### Out of Scope

- Distance markers along the path (total distance in popup only)
- Walking direction arrows or animated dash patterns
- Side panel UI
- Separate waypoint/POI markers along the route
