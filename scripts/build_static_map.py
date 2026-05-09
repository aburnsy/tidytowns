"""Build a print-ready static PDF of the village map for the TidyTowns application.

Two-page A3 landscape PDF:
  * Page 1 — Village core detail (excludes the eastern Liathmore site).
  * Page 2 — Wider area showing Liathmore relative to the core.

Each page is laid out with:
  * Title row across the top (page title left, interactive-version link
    middle, attachment label right) — no raw URLs shown, the link uses a
    friendly display name.
  * Map filling the full page width below the title.
  * Numbered legend grouped by category in horizontal columns below the
    map (so the map gets the full page width).

Run with: uv run --with matplotlib --with contextily --with pyproj python scripts/build_static_map.py
"""

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
import contextily as cx
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
MARKERS_JSON = ROOT / "site" / "docs" / "assets" / "map-data" / "markers.json"
OUT_DIR = ROOT / "applications-2026"
OUT_PDF = OUT_DIR / "village-map.pdf"
OUT_PNG = OUT_DIR / "village-map.png"

INTERACTIVE_URL = "https://aburnsy.github.io/tidytowns/assets/village-map.html"
TRACKER_URL = "https://aburnsy.github.io/tidytowns/"

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
    """Return a new list with per-page numbering grouped by CATEGORY_ORDER."""
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


def draw_north_arrow(ax, x_frac=0.03, y_frac=0.90, size=0.05):
    ax.annotate(
        "N",
        xy=(x_frac, y_frac + size + 0.012),
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


def plot_markers(ax, markers, marker_size=160, fontsize=8):
    for m in markers:
        x, y = to_mercator(*m["coords"])
        ax.scatter(
            x,
            y,
            s=marker_size,
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
    )


def _legend_blocks(markers: list[dict], bog_walk: dict | None, include_bog: bool):
    """Return list of legend blocks in render order.

    Each block is (kind, header_text, color, items) where kind is
    'category' (items is list of marker dicts) or 'bogwalk' (items=None).
    """
    by_cat: dict[str, list[dict]] = {}
    for m in markers:
        by_cat.setdefault(m["category"], []).append(m)
    blocks = []
    for cat in CATEGORY_ORDER:
        items = by_cat.get(cat, [])
        if not items:
            continue
        blocks.append(("category", cat, items[0]["color"], items))
    if include_bog and bog_walk:
        label = f"Bog Walk loop ({bog_walk.get('distance', '')})".strip().rstrip("()")
        blocks.append(("bogwalk", label, bog_walk.get("color", "#1B5E20"), None))
    return blocks


def _distribute_blocks(blocks, n_cols):
    """Greedy fill into n columns, balancing total line count per column."""
    col_lines = [0.0] * n_cols
    col_blocks: list[list] = [[] for _ in range(n_cols)]
    for block in blocks:
        items = block[3]
        # 1 header line + N item lines + small gap
        n_lines = 1 + (len(items) if items else 0) + 0.5
        c = col_lines.index(min(col_lines))
        col_blocks[c].append(block)
        col_lines[c] += n_lines
    return col_blocks


def render_legend(ax, markers, bog_walk, include_bog: bool, n_cols: int = 3):
    """Render a horizontal multi-column legend that uses the full ax width."""
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Title
    ax.text(
        0.0,
        1.02,
        "Map legend",
        fontsize=11,
        fontweight="bold",
        va="bottom",
        transform=ax.transAxes,
    )

    blocks = _legend_blocks(markers, bog_walk, include_bog)
    col_blocks = _distribute_blocks(blocks, n_cols)

    col_w = 1.0 / n_cols
    line_h = 0.072
    cat_pad = 0.018
    swatch_x_offset = 0.012
    text_x_offset = 0.030

    for c in range(n_cols):
        x_left = c * col_w + 0.005
        y = 0.97
        for kind, header, color, items in col_blocks[c]:
            if kind == "bogwalk":
                ax.add_line(
                    Line2D(
                        [x_left, x_left + 0.022],
                        [y, y],
                        color=color,
                        lw=2.4,
                        ls=(0, (4, 2)),
                        transform=ax.transAxes,
                    )
                )
                ax.text(
                    x_left + text_x_offset,
                    y,
                    header,
                    fontsize=8.5,
                    fontweight="bold",
                    va="center",
                    transform=ax.transAxes,
                )
                y -= line_h
            else:
                ax.scatter(
                    [x_left + swatch_x_offset],
                    [y],
                    s=50,
                    c=color,
                    edgecolor="white",
                    linewidth=0.8,
                    transform=ax.transAxes,
                )
                ax.text(
                    x_left + text_x_offset,
                    y,
                    header,
                    fontsize=9.5,
                    fontweight="bold",
                    va="center",
                    transform=ax.transAxes,
                )
                y -= line_h
                for m in items:
                    ax.text(
                        x_left + text_x_offset,
                        y,
                        f"{m['number']}.  {m['name']}",
                        fontsize=8,
                        va="center",
                        transform=ax.transAxes,
                    )
                    y -= line_h
                y -= cat_pad


def add_page_chrome(fig, page_title: str):
    """Top-row: page title (left), interactive-version link (centre), attachment label (right). No raw URLs shown."""
    fig.suptitle(
        page_title,
        fontsize=18,
        fontweight="bold",
        y=0.972,
        x=0.025,
        ha="left",
    )
    fig.text(
        0.5,
        0.972,
        "Interactive online version (tap to open)",
        fontsize=10.5,
        ha="center",
        va="center",
        color="#0D47A1",
        url=INTERACTIVE_URL,
        fontstyle="italic",
    )
    fig.text(
        0.975,
        0.972,
        "TidyTowns 2026 application attachment",
        fontsize=10,
        style="italic",
        ha="right",
        va="center",
    )

    # Footer
    fig.text(
        0.025,
        0.018,
        "Public project tracker (tap to open)",
        fontsize=8,
        ha="left",
        color="#0D47A1",
        url=TRACKER_URL,
    )
    fig.text(
        0.975,
        0.018,
        "Tile basemap © OpenStreetMap contributors, © CartoDB.  Map data and marker positions: TMB Tidy Towns committee.",
        fontsize=7,
        ha="right",
        color="#444",
    )


def make_page(
    page_title: str,
    page_markers: list[dict],
    bog_walk: dict | None,
    *,
    include_bog_in_legend: bool,
    bounds_markers: list[dict],
    include_bog_in_bounds: bool,
    basemap_zoom: int,
    pad_x_frac: float,
    pad_y_frac: float,
    scale_bar_m: int,
):
    """Build one page (figure) of the multi-page PDF."""
    fig = plt.figure(figsize=(16.54, 11.69))  # A3 landscape inches

    gs = fig.add_gridspec(
        nrows=2,
        ncols=1,
        height_ratios=[3.6, 1.0],
        hspace=0.06,
        left=0.025,
        right=0.985,
        top=0.93,
        bottom=0.05,
    )

    ax_map = fig.add_subplot(gs[0, 0])
    ax_legend = fig.add_subplot(gs[1, 0])

    # Compute bounds from supplied marker set (and optionally bog walk)
    bx = [to_mercator(*m["coords"])[0] for m in bounds_markers]
    by = [to_mercator(*m["coords"])[1] for m in bounds_markers]
    if include_bog_in_bounds and bog_walk and "path" in bog_walk:
        for lat, lon in bog_walk["path"]:
            x, y = to_mercator(lat, lon)
            bx.append(x)
            by.append(y)
    pad_x = (max(bx) - min(bx)) * pad_x_frac
    pad_y = (max(by) - min(by)) * pad_y_frac
    ax_map.set_xlim(min(bx) - pad_x, max(bx) + pad_x)
    ax_map.set_ylim(min(by) - pad_y, max(by) + pad_y)
    ax_map.set_aspect("equal")
    ax_map.set_xticks([])
    ax_map.set_yticks([])
    for spine in ax_map.spines.values():
        spine.set_linewidth(0.8)

    add_basemap(ax_map, source=cx.providers.OpenStreetMap.Mapnik, zoom=basemap_zoom)
    plot_bog_walk(ax_map, bog_walk)
    plot_markers(ax_map, page_markers, marker_size=170, fontsize=8)
    draw_north_arrow(ax_map)
    draw_scale_bar(ax_map, length_m=scale_bar_m)

    render_legend(ax_legend, page_markers, bog_walk, include_bog=include_bog_in_legend, n_cols=3)

    add_page_chrome(fig, page_title)
    return fig


def main():
    data = load_data()
    bog_walk = data.get("bogWalk")

    # Page 1 — village core (excludes eastern Liathmore site).
    # Liathmore sits at lon -7.66861; village core lies west of -7.69.
    core_markers_raw = [m for m in data["markers"] if m["coords"][1] < -7.69]
    core_markers = assign_numbers(core_markers_raw)

    # Page 2 — full extent including Liathmore.
    wider_markers = assign_numbers(data["markers"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fig_core = make_page(
        page_title="Two Mile Borris — Village Core",
        page_markers=core_markers,
        bog_walk=bog_walk,
        include_bog_in_legend=False,  # bog walk only fully visible on wider page
        bounds_markers=core_markers,
        include_bog_in_bounds=False,  # tighter view of the village itself
        basemap_zoom=17,
        pad_x_frac=0.06,
        pad_y_frac=0.18,
        scale_bar_m=200,
    )

    fig_wider = make_page(
        page_title="Two Mile Borris — Wider Area (incl. Liathmore)",
        page_markers=wider_markers,
        bog_walk=bog_walk,
        include_bog_in_legend=True,
        bounds_markers=wider_markers,
        include_bog_in_bounds=True,
        basemap_zoom=15,
        pad_x_frac=0.04,
        pad_y_frac=0.10,
        scale_bar_m=500,
    )

    with PdfPages(OUT_PDF) as pdf:
        pdf.savefig(fig_core, dpi=300)
        pdf.savefig(fig_wider, dpi=300)
    print(f"Wrote {OUT_PDF} (2 pages)")

    # PNG = village-core page only (used as a thumbnail / quick preview)
    fig_core.savefig(OUT_PNG, dpi=200, bbox_inches="tight")
    print(f"Wrote {OUT_PNG}")

    plt.close(fig_core)
    plt.close(fig_wider)


if __name__ == "__main__":
    main()
