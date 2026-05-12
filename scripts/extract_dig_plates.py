"""Extract placeholder photos from final-report PDFs for dig markers + heritage pages.

These are LOW-RES placeholders rendered from the final report PDFs. TII has
offered to provide high-resolution versions from the project archive; this
script gets us something usable in the meantime.
"""

import json
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "site" / "docs" / "assets" / "map-data" / "photos"
HERITAGE_IMG = ROOT / "site" / "docs" / "assets" / "heritage"

PDFS = {
    "ar31_v1": Path("C:/Users/andre/Downloads/q8120050v.pdf"),
    "ar33": Path("C:/Users/andre/Downloads/n871ch32b.pdf"),
    "ar32": Path("C:/Users/andre/Downloads/q237x682h.pdf"),
    "ar36": Path("C:/Users/andre/Downloads/jd47gb342.pdf"),
}

CREDIT_TII = "Valerie J. Keeley Ltd / TII"
CREDIT_STUDIOLABS = "Studio Labs / Valerie J. Keeley Ltd / TII"
CREDIT_AIRSHOTS = "Airshots Ltd / Valerie J. Keeley Ltd / TII"

PLACEHOLDER_NOTE = "Placeholder extracted from final report PDF; high-resolution version pending."


def render_crop(pdf_key: str, page_index: int, position: str, dpi: int = 250) -> bytes:
    """Render a PDF page region as JPEG bytes.

    position: 'full' = whole page, 'top' = top half, 'bottom' = bottom half.
    """
    doc = pymupdf.open(PDFS[pdf_key])
    page = doc[page_index]
    rect = page.rect
    if position == "top":
        clip = pymupdf.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + rect.height * 0.52)
    elif position == "bottom":
        clip = pymupdf.Rect(rect.x0, rect.y0 + rect.height * 0.48, rect.x1, rect.y1)
    else:
        clip = rect
    pix = page.get_pixmap(dpi=dpi, clip=clip)
    data = pix.tobytes("jpeg", jpg_quality=85)
    doc.close()
    return data


# Each entry: (marker_id, pdf_key, page_index_1based, position, filename, caption, credit)
PLATES = [
    # ---- AR 31 (Borris & Blackcastle dig) ----
    ("dig_ar31", "ar31_v1", 298, "top",    "plate01-aerial-ar31.jpg",
     "Aerial view of Site AR 31 with adjacent monuments, looking northwest", CREDIT_STUDIOLABS),
    ("dig_ar31", "ar31_v1", 302, "bottom", "plate10-mill-complex-mid-excavation.jpg",
     "Mid-excavation view of the medieval mill complex, looking south-southwest", CREDIT_TII),
    ("dig_ar31", "ar31_v1", 303, "top",    "plate11-mill-house-wheel-pit.jpg",
     "Mill house foundation and wheel pit, looking west-southwest", CREDIT_TII),
    ("dig_ar31", "ar31_v1", 304, "full",   "plate13-aerial-mill-complex.jpg",
     "Aerial view of the mill complex: tail race, wheel pit, mill house and part of the head race", CREDIT_AIRSHOTS),
    ("dig_ar31", "ar31_v1", 305, "top",    "plate14-timber5-lap-joint.jpg",
     "Lap joint on in situ Timber 5, looking north-northwest (the 5m+ oak from the wheel pit)", CREDIT_TII),
    ("dig_ar31", "ar31_v1", 314, "full",   "plate25-well-coin-hoard.jpg",
     "Excavation of the well [c459] containing the Edward I coin hoard and the carved bone handle", CREDIT_TII),
    ("dig_ar31", "ar31_v1", 320, "top",    "plate36-limekiln.jpg",
     "19th-century stone limekiln in Blackcastle townland", CREDIT_TII),
    ("dig_ar31", "ar31_v1", 322, "top",    "plate40-bone-spindle-whorl.jpg",
     "Bone spindle whorl carved from a cattle femur head (E2374:1283)", CREDIT_TII),
    ("dig_ar31", "ar31_v1", 322, "bottom", "plate41-bone-castle-handle.jpg",
     "The bone castle: decorated handle carved from a horse metacarpal, recovered from the same well as the coin hoard (E2374:233)", CREDIT_TII),
    ("dig_ar31", "ar31_v1", 323, "top",    "plate42-penannular-brooch.jpg",
     "Copper-alloy penannular brooch with zoomorphic terminals (E2374:476)", CREDIT_TII),
    ("dig_ar31", "ar31_v1", 323, "bottom", "plate43-lead-sexfoil-mounts.jpg",
     "Lead 'sexfoil' flower-shaped mounts, six cast from one mould, mid-14th century (E2374:1287-1292)", CREDIT_TII),
    ("dig_ar31", "ar31_v1", 324, "top",    "plate44-coin-edward-i-london.jpg",
     "Edward I penny, London mint, autumn 1280 (E2374:19)", CREDIT_TII),
    ("dig_ar31", "ar31_v1", 326, "bottom", "plate52-coin-flanders.jpg",
     "Flemish coin: Valeran I or II, Lords of Ligny, c.1310 (E2374:342), found in the AR 31 hoard", CREDIT_TII),

    # ---- AR 33 (Ringfort & Enclosure D) ----
    ("dig_ar33", "ar33", 511, "top",    "plate01-aerial-ar33.jpg",
     "Aerial view of Site AR 33 with adjacent sites and monuments, looking northwest", CREDIT_STUDIOLABS),
    ("dig_ar33", "ar33", 512, "bottom", "plate04-enclosure-d-aerial.jpg",
     "Aerial view of Enclosure D with its south-eastern entrance, looking west", CREDIT_AIRSHOTS),
    ("dig_ar33", "ar33", 513, "bottom", "plate06-enclosure-d-cranium.jpg",
     "Northern terminus of the south-eastern ditch [c1457] of Enclosure D, with human cranium fragment in situ", CREDIT_TII),
    ("dig_ar33", "ar33", 515, "bottom", "plate10-cattle-burial.jpg",
     "Mid-excavation view of the bovine burial pit [c1647] inside Enclosure D: bones of a mature cow placed in crisscrossed layers on three small wooden stakes", CREDIT_TII),
    ("dig_ar33", "ar33", 516, "top",    "plate11-aerial-enclosures-a-b-c.jpg",
     "Aerial view of Enclosures A, B and C: the early medieval plectrum-shaped enclosure, the overlying ringfort, and the later rectangular expansion", CREDIT_STUDIOLABS),
    ("dig_ar33", "ar33", 519, "bottom", "plate18-ringfort-aerial.jpg",
     "Aerial view of Enclosure A (the ringfort), showing interior features, looking southeast", CREDIT_AIRSHOTS),
    ("dig_ar33", "ar33", 521, "bottom", "plate22-metalworking-hearth.jpg",
     "Metalworking hearth feature [c130] inside Enclosure A, dated 680-774 AD", CREDIT_TII),
    ("dig_ar33", "ar33", 529, "top",    "plate35-elderly-male-burial.jpg",
     "Excavation of burial SK1 [c1001], an elderly male, in the AR 33 cemetery", CREDIT_TII),
    ("dig_ar33", "ar33", 537, "bottom", "plate51-ring-pin.jpg",
     "Copper-alloy ring-pin (E2376:68) - found tucked beneath the vertebrae of an adult woman's neck in the AR 33 cemetery", CREDIT_TII),
    ("dig_ar33", "ar33", 539, "bottom", "plate55-sandstone-axe.jpg",
     "Polished sandstone axe-head from Site AR 33 (E2376:332)", CREDIT_TII),

    # ---- AR 32 (Bronze Age cremation cemetery) ----
    ("dig_ar32", "ar32", 106, "top",    "plate01-aerial-ar32.jpg",
     "Aerial view of Site AR 32, showing the cremation cemetery's setting in the field", CREDIT_TII),
    ("dig_ar32", "ar32", 108, "top",    "plate05-cremation-pit-c5.jpg",
     "Cremation pit [c5], dated 1603-1427 cal BC, with a large burnt bone fragment visible (scale 0.40m)", CREDIT_TII),

    # ---- AR 36 (cremation cemetery & smithing site) ----
    ("dig_ar36", "ar36", None, None, None, None, None),  # placeholder, AR 36 plate pages not yet located
]


def main() -> None:
    HERITAGE_IMG.mkdir(parents=True, exist_ok=True)
    captions_per_marker: dict[str, list[dict]] = {}

    for marker_id, pdf_key, page_1based, position, filename, caption, credit in PLATES:
        if page_1based is None:
            continue
        out_dir = PHOTOS / marker_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / filename
        try:
            data = render_crop(pdf_key, page_1based - 1, position)
        except Exception as exc:
            print(f"  FAILED {filename}: {exc}")
            continue
        out_path.write_bytes(data)
        full_caption = f"{caption}. {PLACEHOLDER_NOTE} (Source: {credit})"
        captions_per_marker.setdefault(marker_id, []).append(
            {"file": filename, "caption": full_caption}
        )
        size_kb = len(data) // 1024
        print(f"  wrote {out_path.relative_to(ROOT)}  ({size_kb} kB)")

    # Write _captions.json for each marker
    for marker_id, caps in captions_per_marker.items():
        cap_path = PHOTOS / marker_id / "_captions.json"
        cap_path.write_text(json.dumps(caps, indent=2, ensure_ascii=False))
        print(f"  wrote {cap_path.relative_to(ROOT)}  ({len(caps)} captions)")


if __name__ == "__main__":
    main()
