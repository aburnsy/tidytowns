"""Sync trimmed content from FINAL-application-text.md back into per-section files.

FINAL-application-text.md is the working/copy-paste source. Per-section files
(01-community.md, 02-streetscape.md, etc.) are what build_entry_form.py reads.
This script keeps them in sync after trims.

Usage:
  uv run python scripts/sync_final_to_sections.py
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
FINAL = ROOT / "private" / "application-2026" / "FINAL-application-text.md"
APP_DIR = ROOT / "private" / "application-2026"

# H2 heading prefix in FINAL.md -> per-section filename
SECTION_FILES = {
    "01 - Community Involvement and Spirit": "01-community.md",
    "02 - Streetscape and Public Places": "02-streetscape.md",
    "03 - Green Spaces and Landscaping": "03-green-spaces.md",
    "04 - Nature and Biodiversity": "04-nature-biodiversity.md",
    "05 - Sustainability": "05-sustainability.md",
    "06 - Tidiness and Litter Control": "06-tidiness.md",
    "07 - Residential Streets and Housing Areas": "07-residential.md",
    "08 - Approach Roads, Streets and Lanes": "08-approach-roads.md",
}


def split_sections(text: str) -> dict[str, tuple[str, str]]:
    """Split FINAL text on H2 headings. Returns {heading: (full_heading_line, body)}."""
    out = {}
    lines = text.splitlines()
    current_heading = None
    current_full = None
    buf: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if current_heading is not None:
                out[current_heading] = (current_full, "\n".join(buf).strip())
            current_full = line
            current_heading = line[3:].strip()
            buf = []
        else:
            buf.append(line)
    if current_heading is not None:
        out[current_heading] = (current_full, "\n".join(buf).strip())
    return out


def convert_h3_to_bold_inline(body: str) -> str:
    """Convert H3 subheadings to bold inline labels: '### Title' + body -> '**Title.** body'.

    Each bold-inline paragraph is separated by a blank line so build_entry_form.py
    (which splits on blank lines) treats them as distinct paragraphs.
    """
    paragraphs: list[str] = []
    lines = body.splitlines()
    i = 0
    # Capture any leading paragraphs before the first H3 (preamble)
    preamble: list[str] = []
    current_para: list[str] = []
    while i < len(lines) and not lines[i].startswith("### "):
        if lines[i].strip():
            current_para.append(lines[i])
        else:
            if current_para:
                preamble.append(" ".join(current_para).strip())
                current_para = []
        i += 1
    if current_para:
        preamble.append(" ".join(current_para).strip())
        current_para = []
    paragraphs.extend(preamble)

    # Process each H3 block
    while i < len(lines):
        if lines[i].startswith("### "):
            heading = lines[i][4:].strip().rstrip(".")
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            # Collect content paragraphs until next H3 or end
            content_parts: list[str] = []
            current_para = []
            while i < len(lines) and not lines[i].startswith("### "):
                if lines[i].strip():
                    current_para.append(lines[i])
                else:
                    if current_para:
                        content_parts.append(" ".join(current_para).strip())
                        current_para = []
                i += 1
            if current_para:
                content_parts.append(" ".join(current_para).strip())
                current_para = []
            if content_parts:
                paragraphs.append(f"**{heading}.** {content_parts[0]}")
                paragraphs.extend(content_parts[1:])
            else:
                paragraphs.append(f"**{heading}.**")
        else:
            i += 1

    return "\n\n".join(paragraphs).strip()


def convert_h3_to_h2_for_community(body: str) -> str:
    """Community file uses H2 for sub-questions (the script's parse_community_md keys on ##)."""
    return re.sub(r"^### ", "## ", body, flags=re.MULTILINE).strip()


def main():
    final_text = FINAL.read_text(encoding="utf-8")
    sections = split_sections(final_text)

    for heading_prefix, filename in SECTION_FILES.items():
        # Find the matching section by prefix
        match_key = None
        for k in sections:
            if k.startswith(heading_prefix):
                match_key = k
                break
        if match_key is None:
            print(f"  SKIP {filename}: no section starting with '{heading_prefix}'")
            continue

        full_heading, body = sections[match_key]
        # Convert "## 01 - Community ..." -> "# 01 - Community ..."
        h1 = "# " + full_heading[3:]

        if filename == "01-community.md":
            converted = convert_h3_to_h2_for_community(body)
        else:
            converted = convert_h3_to_bold_inline(body)

        out = f"{h1}\n\n{converted}\n"
        target = APP_DIR / filename
        target.write_text(out, encoding="utf-8", newline="\n")
        word_count = len([w for w in re.sub(r"https?://\S+|[#*`\[\]\(\)]", "", converted).split() if w])
        print(f"  {filename:<30} {word_count:>5} words")

    print()
    print(f"Synced {len(SECTION_FILES)} section files from {FINAL.name}.")


if __name__ == "__main__":
    main()
