"""Build a print-ready static PDF of the village map for the TidyTowns application.

Two panels on a single landscape A3 page:
  * Main panel: detail of the village core (excludes the eastern Liathmore site).
  * Inset panel: full extent showing Liathmore monastic site relative to the core.
Plus a numbered legend grouped by category.

Run with: uv run --with matplotlib --with contextily --with pyproj python scripts/build_static_map.py
"""

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import contextily as cx
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
MARKERS_JSON = ROOT / "site" / "docs" / "assets" / "map-data" / "markers.json"
OUT_DIR = ROOT / "private" / "application-2026" / "attachments"
OUT_PDF = OUT_DIR / "village-map.pdf"
OUT_PNG = OUT_DIR / "village-map.png"

CATEGORY_ORDER = [
    "Village Features",
    "Green Spaces & Nature",
    "Businesses",
    "School",
    "Housing Estates",
    "Approach Roads",
    "Other",
]

WGS84_TO_MERC = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)


def to_mercator(lat: float, lon: float) -> tuple[float, float]:
    x, y = WGS84_TO_MERC.transform(lon, lat)
    return x, y


def load_data() -> dict:
    with open(MARKERS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def assign_numbers(markers: list[dict]) -> list[dict]:
    """Assign marker numbers grouped by category in CATEGORY_ORDER."""
    by_cat: dict[str, list[dict]] = {c: [] for c in CATEGORY_ORDER}
    for m in markers:
        by_cat.setdefault(m["category"], []).append(m)
    numbered = []
    n = 1
    for cat in CATEGORY_ORDER:
        for m in sorted(by_cat.get(cat, []), key=lambda x: x["name"]):
            m = dict(m)
            m["number"] = n
            numbered.append(m)
            n += 1
    return numbered


def add_basemap(ax, source, zoom):
    try:
        cx.add_basemap(ax, source=source, zoom=zoom, attribution_size=6)
    except Exception as e:
        print(f"  basemap fetch failed ({e}); falling back to OSM")
        cx.add_basemap(ax, source=cx.providers.OpenStreetMap.Mapnik, zoom=zoom, attribution_size=6)


def draw_north_arrow(ax, x_frac=0.04, y_frac=0.92, size=0.06):
    ax.annotate(
        "N",
        xy=(x_frac, y_frac + size + 0.01),
        xycoords="axes fraction",
        ha="center",
        va="bottom",
        fontsize=11,
        fontweight="bold",
    )
    ax.annotate(
        "",
        xy=(x_frac, y_frac + size),
        xytext=(x_frac, y_frac),
        xycoords="axes fraction",
        arrowprops=dict(arrowstyle="-|>", color="black", lw=1.6, mutation_scale=18),
    )


def draw_scale_bar(ax, length_m=500):
    """Approximate scale bar in metres for a Web Mercator axis at this latitude."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    # latitude scale correction at ~52.67N
    lat = 52.672
    metres_per_unit = math.cos(math.radians(lat))
    bar_units = length_m / metres_per_unit

    pad_x = (x1 - x0) * 0.04
    pad_y = (y1 - y0) * 0.04
    bx0 = x1 - pad_x - bar_units
    bx1 = x1 - pad_x
    by = y0 + pad_y

    ax.plot([bx0, bx1], [by, by], color="black", lw=3, solid_capstyle="butt")
    ax.plot([bx0, bx0], [by, by + (y1 - y0) * 0.008], color="black", lw=2)
    ax.plot([bx1, bx1], [by, by + (y1 - y0) * 0.008], color="black", lw=2)
    ax.text(
        (bx0 + bx1) / 2,
        by + (y1 - y0) * 0.012,
        f"{length_m} m",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )


def plot_markers(ax, markers, fontsize=8):
    for m in markers:
        x, y = to_mercator(*m["coords"])
        ax.scatter(
            x,
            y,
            s=160,
            c=m["color"],
            edgecolor="white",
            linewidth=1.6,
            zorder=5,
        )
        ax.text(
            x,
            y,
            str(m["number"]),
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight="bold",
            color="white",
            zorder=6,
        )


def plot_bog_walk(ax, bog_walk):
    if not bog_walk or "path" not in bog_walk:
        return
    xs, ys = [], []
    for lat, lon in bog_walk["path"]:
        x, y = to_mercator(lat, lon)
        xs.append(x)
        ys.append(y)
    ax.plot(
        xs,
        ys,
        color=bog_walk.get("color", "#1B5E20"),
        lw=2.4,
        ls=(0, (4, 2)),
        zorder=4,
        label="Bog Walk loop",
    )


def render_legend(ax, markers, bog_walk):
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax.text(
        0.0,
        0.99,
        "Map legend",
        fontsize=13,
        fontweight="bold",
        va="top",
        transform=ax.transAxes,
    )

    by_cat: dict[str, list[dict]] = {}
    for m in markers:
        by_cat.setdefault(m["category"], []).append(m)

    y = 0.95
    line_h = 0.0235
    cat_pad = 0.010

    for cat in CATEGORY_ORDER:
        items = by_cat.get(cat, [])
        if not items:
            continue
        color = items[0]["color"]
        ax.scatter([0.02], [y], s=55, c=color, edgecolor="white", linewidth=0.8, transform=ax.transAxes)
        ax.text(0.07, y, cat, fontsize=9.5, fontweight="bold", va="center", transform=ax.transAxes)
        y -= line_h
        for m in items:
            ax.text(
                0.07,
                y,
                f"{m['number']}.  {m['name']}",
                fontsize=8,
                va="center",
                transform=ax.transAxes,
            )
            y -= line_h
        y -= cat_pad

    # Bog walk swatch
    if bog_walk:
        ax.add_line(
            Line2D(
                [0.01, 0.06],
                [y, y],
                color=bog_walk.get("color", "#1B5E20"),
                lw=2.4,
                ls=(0, (4, 2)),
                transform=ax.transAxes,
            )
        )
        ax.text(
            0.07,
            y,
            f"Bog Walk loop ({bog_walk.get('distance', '')})",
            fontsize=8.5,
            fontweight="bold",
            va="center",
            transform=ax.transAxes,
        )


def main():
    data = load_data()
    markers = assign_numbers(data["markers"])
    bog_walk = data.get("bogWalk")

    # Village core panel excludes the eastern Liathmore site (caught by the inset).
    # Liathmore sits at lon -7.66861; the village core lies west of -7.69.
    core_markers = [m for m in markers if m["coords"][1] < -7.69]

    fig = plt.figure(figsize=(16.54, 11.69))  # A3 landscape inches
    gs = fig.add_gridspec(
        nrows=2,
        ncols=2,
        width_ratios=[2.4, 1.0],
        height_ratios=[2.4, 1.0],
        wspace=0.04,
        hspace=0.10,
        left=0.025,
        right=0.985,
        top=0.93,
        bottom=0.04,
    )

    ax_main = fig.add_subplot(gs[0, 0])
    ax_inset = fig.add_subplot(gs[1, 0])
    ax_legend = fig.add_subplot(gs[:, 1])

    # --- Main detail panel: village core (bounded by markers only, not bog walk) ---
    core_xy = [to_mercator(*m["coords"]) for m in core_markers]
    bog_xy = [to_mercator(lat, lon) for lat, lon in (bog_walk["path"] if bog_walk else [])]
    xs = [p[0] for p in core_xy]
    ys = [p[1] for p in core_xy]
    pad_x = (max(xs) - min(xs)) * 0.18
    pad_y = (max(ys) - min(ys)) * 0.30
    ax_main.set_xlim(min(xs) - pad_x, max(xs) + pad_x)
    ax_main.set_ylim(min(ys) - pad_y, max(ys) + pad_y)
    ax_main.set_aspect("equal")
    ax_main.set_xticks([])
    ax_main.set_yticks([])
    for spine in ax_main.spines.values():
        spine.set_linewidth(0.8)

    add_basemap(ax_main, source=cx.providers.OpenStreetMap.Mapnik, zoom=17)
    plot_bog_walk(ax_main, bog_walk)
    plot_markers(ax_main, core_markers, fontsize=8)
    draw_north_arrow(ax_main)
    draw_scale_bar(ax_main, length_m=200)

    ax_main.set_title("Village core", fontsize=12, fontweight="bold", loc="left", pad=8)

    # --- Inset overview panel: full extent including Liathmore ---
    all_markers_xy = [to_mercator(*m["coords"]) for m in markers]
    xs2 = [p[0] for p in all_markers_xy] + [p[0] for p in bog_xy]
    ys2 = [p[1] for p in all_markers_xy] + [p[1] for p in bog_xy]
    pad_x2 = (max(xs2) - min(xs2)) * 0.08
    pad_y2 = (max(ys2) - min(ys2)) * 0.20
    ax_inset.set_xlim(min(xs2) - pad_x2, max(xs2) + pad_x2)
    ax_inset.set_ylim(min(ys2) - pad_y2, max(ys2) + pad_y2)
    ax_inset.set_aspect("equal")
    ax_inset.set_xticks([])
    ax_inset.set_yticks([])
    for spine in ax_inset.spines.values():
        spine.set_linewidth(0.8)

    add_basemap(ax_inset, source=cx.providers.OpenStreetMap.Mapnik, zoom=14)
    plot_bog_walk(ax_inset, bog_walk)
    # smaller markers in the inset
    for m in markers:
        x, y = to_mercator(*m["coords"])
        ax_inset.scatter(x, y, s=60, c=m["color"], edgecolor="white", linewidth=1, zorder=5)
        ax_inset.text(x, y, str(m["number"]), ha="center", va="center", fontsize=5.5, fontweight="bold", color="white", zorder=6)
    ax_inset.set_title("Wider area (incl. Liathmore)", fontsize=11, fontweight="bold", loc="left", pad=6)

    # --- Legend panel ---
    render_legend(ax_legend, markers, bog_walk)

    # --- Page title and footer ---
    fig.suptitle(
        "Two Mile Borris — Village Map",
        fontsize=18,
        fontweight="bold",
        y=0.975,
        x=0.04,
        ha="left",
    )
    fig.text(
        0.97,
        0.975,
        "TidyTowns 2026 application attachment",
        fontsize=10,
        style="italic",
        ha="right",
        va="top",
    )
    fig.text(
        0.04,
        0.025,
        "Tile basemap © OpenStreetMap contributors, © CartoDB.  Map data and marker positions: TMB Tidy Towns committee.",
        fontsize=7,
        ha="left",
        color="#444",
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, dpi=300, bbox_inches="tight")
    fig.savefig(OUT_PNG, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUT_PDF}")
    print(f"Wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
