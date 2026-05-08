"""Resize (if needed) and copy scraped tmbvillage.ie images into map photo dirs."""
from PIL import Image
from pathlib import Path
import shutil

SRC = Path(r"C:\Users\andre\OneDrive\Documents\Development\tidytowns\.scratch\tmb_imgs")
DST = Path(r"C:\Users\andre\OneDrive\Documents\Development\tidytowns\site\docs\assets\map-data\photos")

# (source filename, target marker, target filename, max width)
JOBS = [
    ("d9aee9_ab4e3b65b0bf4a97853db3f362a6f395_mv2.jpg", "blackcastle", "castle-streetview-summer.jpg", 1600),
    ("d9aee9_b23646cd78bc40de9cba2778192c4dfc_mv2.jpg", "church", "church-deep-clean-dec-2023.jpg", 1600),
    ("d9aee9_77bd9276308240b6a63dc576f98466a2_mv2.jpg", "sensory_garden", "sensory-garden-aerial-spring.jpg", 1800),
    ("d9aee9_16504e5920da4a54bba0eca6c02fc26b_mv2.jpg", "monument", "christmas-lights-tractor-parade-dec-2023.jpg", 1600),
    ("d9aee9_ae2ed334c24c4b6cbb9c804374ee7105_mv2.jpg", "approach_east", "lions-cheque-at-welcome-sign-2025.jpg", 1600),
    ("d9aee9_bc5b961886e24f9c87eb61c717aab1cc_mv2.jpg", "bog_walk", "lions-club-bog-walk-cheque-2025.jpg", 1600),
    ("d9aee9_8d8e5d076df14bb39f73b76e4674d538_mv2.jpg", "new_cemetery_entrance", "graveyard-extension-construction-spring-2025.jpg", 1600),
    ("d9aee9_b7c6465d5718438fb454b65bb571f2c1f000.jpg", "castle_park", "estate-aerial-spring-2025.jpg", 1600),
]

for src_name, marker, dst_name, max_w in JOBS:
    src = SRC / src_name
    dst_dir = DST / marker
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / dst_name
    im = Image.open(src)
    w, h = im.size
    print(f"{marker}/{dst_name}: source {w}x{h} ({src.stat().st_size/1024:.0f} KB)")
    if w > max_w:
        ratio = max_w / w
        new_size = (max_w, int(h * ratio))
        im = im.convert("RGB")
        im = im.resize(new_size, Image.LANCZOS)
        im.save(dst, "JPEG", quality=85, optimize=True)
        print(f"  -> resized to {new_size[0]}x{new_size[1]} ({dst.stat().st_size/1024:.0f} KB)")
    else:
        if im.mode != "RGB":
            im = im.convert("RGB")
            im.save(dst, "JPEG", quality=90, optimize=True)
        else:
            shutil.copy2(src, dst)
        print(f"  -> copied as-is ({dst.stat().st_size/1024:.0f} KB)")
