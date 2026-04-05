#!/bin/bash
# new-project.sh - Interactive script to create a new TidyTowns project
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_DIR="$SCRIPT_DIR/../site/docs/projects"

# ──────────────────────────────────────────────
# 1. Auto-generate next project number
# ──────────────────────────────────────────────
get_next_number() {
  local max=0
  for dir in "$PROJECTS_DIR"/[0-9][0-9][0-9]-*/; do
    [ -d "$dir" ] || continue
    local base
    base="$(basename "$dir")"
    local num="${base%%\-*}"
    # Strip leading zeros for arithmetic
    local n=$((10#$num))
    [ "$n" -gt "$max" ] && max=$n
  done
  echo $((max + 1))
}

next_num=$(get_next_number)
padded_num=$(printf "%03d" "$next_num")

echo ""
echo "============================================"
echo "  New TidyTowns Project  (next #: $padded_num)"
echo "============================================"
echo ""

# ──────────────────────────────────────────────
# 2. Title
# ──────────────────────────────────────────────
read -rp "Project title: " title
if [ -z "$title" ]; then
  echo "Error: title is required." >&2
  exit 1
fi

# Build slug from title
slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//')

# ──────────────────────────────────────────────
# 3. Category tags
# ──────────────────────────────────────────────
echo ""
echo "Categories (enter numbers separated by spaces):"
echo "  1) community"
echo "  2) streetscape"
echo "  3) green-spaces"
echo "  4) nature-biodiversity"
echo "  5) sustainability"
echo "  6) tidiness"
echo "  7) residential"
echo "  8) approach-roads"
echo ""
read -rp "Tag numbers (e.g. 1 3 5): " tag_nums

declare -a CATEGORY_NAMES
CATEGORY_NAMES[1]="community"
CATEGORY_NAMES[2]="streetscape"
CATEGORY_NAMES[3]="green-spaces"
CATEGORY_NAMES[4]="nature-biodiversity"
CATEGORY_NAMES[5]="sustainability"
CATEGORY_NAMES[6]="tidiness"
CATEGORY_NAMES[7]="residential"
CATEGORY_NAMES[8]="approach-roads"

tags_yaml=""
for num in $tag_nums; do
  if [[ "$num" =~ ^[1-8]$ ]]; then
    tags_yaml="${tags_yaml}  - ${CATEGORY_NAMES[$num]}"$'\n'
  fi
done
if [ -z "$tags_yaml" ]; then
  tags_yaml="  - community"$'\n'
  echo "(No valid tags selected; defaulting to 'community')"
fi

# ──────────────────────────────────────────────
# 4. Status
# ──────────────────────────────────────────────
echo ""
echo "Status options:  Planned 2026 | Planned 2027 | Active | Completed | On Hold"
read -rp "Status [Planned 2026]: " status
status="${status:-Planned 2026}"

# ──────────────────────────────────────────────
# 5. Owner (shortname or blank)
# ──────────────────────────────────────────────
read -rp "Owner shortname (or blank): " owner

# ──────────────────────────────────────────────
# 6. Cost estimate
# ──────────────────────────────────────────────
read -rp "Cost estimate (e.g. €0 or €50-100) [€0]: " cost_estimate
cost_estimate="${cost_estimate:-€0}"

# ──────────────────────────────────────────────
# 7. Benefit
# ──────────────────────────────────────────────
echo ""
echo "Benefit: 1) High  2) Medium  3) Low"
read -rp "Benefit [1]: " benefit_num
case "${benefit_num:-1}" in
  2) benefit="Medium" ;;
  3) benefit="Low" ;;
  *) benefit="High" ;;
esac

# ──────────────────────────────────────────────
# 8. Volunteer hours
# ──────────────────────────────────────────────
read -rp "Volunteer hours estimate [TBD]: " volunteer_hours
volunteer_hours="${volunteer_hours:-TBD}"

# ──────────────────────────────────────────────
# 9. Inspired by
# ──────────────────────────────────────────────
read -rp "Inspired by ['']: " inspired_by

# ──────────────────────────────────────────────
# 10. Special award (optional)
# ──────────────────────────────────────────────
echo ""
echo "Special award (optional):"
echo "  1) Endeavour Award"
echo "  2) Sustainability & Circular Economy"
echo "  3) Leave No Trace"
echo "  4) Inclusion Award"
echo "  5) Active Travel"
echo "  6) Tiny TidyTowns"
echo "  0) None"
read -rp "Special award [0]: " award_num

declare -a AWARD_NAMES
AWARD_NAMES[1]="Endeavour Award"
AWARD_NAMES[2]="Sustainability & Circular Economy"
AWARD_NAMES[3]="Leave No Trace"
AWARD_NAMES[4]="Inclusion Award"
AWARD_NAMES[5]="Active Travel"
AWARD_NAMES[6]="Tiny TidyTowns"

special_award=""
if [[ "${award_num:-0}" =~ ^[1-6]$ ]]; then
  special_award="${AWARD_NAMES[$award_num]}"
fi

# ──────────────────────────────────────────────
# 11. Description
# ──────────────────────────────────────────────
echo ""
read -rp "Description (single line): " description

# ──────────────────────────────────────────────
# 12. Create the project folder and index.md
# ──────────────────────────────────────────────
folder_name="${padded_num}-${slug}"
project_dir="$PROJECTS_DIR/$folder_name"

if [ -d "$project_dir" ]; then
  echo "Error: folder already exists: $project_dir" >&2
  exit 1
fi

mkdir -p "$project_dir"

# Build optional fields
special_award_line=""
if [ -n "$special_award" ]; then
  special_award_line="special_award: \"$special_award\""$'\n'
fi

inspired_by_line=""
if [ -n "$inspired_by" ]; then
  inspired_by_line="inspired_by: \"$inspired_by\""$'\n'
fi

owner_val="${owner:-}"

cat > "$project_dir/index.md" <<MDEOF
---
title: "$title"
tags:
${tags_yaml}status: "$status"
owner: "$owner_val"
cost_estimate: "$cost_estimate"
benefit: "$benefit"
volunteer_hours: "$volunteer_hours"
${inspired_by_line}${special_award_line}---

# $title

## Description

${description:-*No description provided yet.*}

## Tasks

*Tasks will be added when the project is approved and assigned.*

## Have your say

[Comment on this project](../../submit-idea.md) | [Propose a new project](../../propose-project.md)
MDEOF

echo ""
echo "Created: $project_dir/index.md"
echo "Project #$padded_num: $title"
