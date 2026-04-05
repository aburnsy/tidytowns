#!/bin/bash
# generate-index.sh - Rebuild the project listing in site/docs/index.md
# Scans all project index.md files, extracts frontmatter, and replaces content
# between <!-- PROJECT_LIST_START --> and <!-- PROJECT_LIST_END --> markers.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_DIR="$SCRIPT_DIR/../site/docs/projects"
INDEX_FILE="$SCRIPT_DIR/../site/docs/index.md"

# ──────────────────────────────────────────────
# Helper: read a single frontmatter field from a file
# $1 = file, $2 = field name
# ──────────────────────────────────────────────
read_field() {
  local file="$1" field="$2"
  grep -m1 "^${field}:" "$file" 2>/dev/null \
    | sed "s/^${field}: *//" \
    | sed 's/^"//;s/"$//' \
    | sed "s/^'//;s/'$//"
}

# ──────────────────────────────────────────────
# Helper: count task files in a project dir (not templates)
# ──────────────────────────────────────────────
count_tasks() {
  local dir="$1"
  find "$dir" -maxdepth 1 -name "task-*.md" ! -name "task-*-template.md" 2>/dev/null | wc -l | tr -d ' '
}

count_done_tasks() {
  local dir="$1"
  local count=0
  for f in "$dir"/task-*.md; do
    [ -f "$f" ] || continue
    # Skip templates
    case "$f" in *-template.md) continue ;; esac
    local s
    s=$(read_field "$f" "status")
    [ "$s" = "done" ] && count=$((count + 1))
  done
  echo "$count"
}

# ──────────────────────────────────────────────
# Build project lines
# ──────────────────────────────────────────────
echo "Scanning projects in $PROJECTS_DIR ..."

normal_lines=""
wontdo_lines=""
project_count=0

for proj_dir in "$PROJECTS_DIR"/[0-9][0-9][0-9]-*/; do
  [ -d "$proj_dir" ] || continue
  index_file="$proj_dir/index.md"
  [ -f "$index_file" ] || continue

  folder_name="$(basename "$proj_dir")"
  echo "  Processing $folder_name"

  title=$(read_field "$index_file" "title")
  status=$(read_field "$index_file" "status")
  cost=$(read_field "$index_file" "cost_estimate")
  benefit=$(read_field "$index_file" "benefit")
  owner=$(read_field "$index_file" "owner")
  special_award=$(read_field "$index_file" "special_award")

  # Defaults
  [ -z "$title" ]   && title="$folder_name"
  [ -z "$status" ]  && status="Unknown"
  [ -z "$cost" ]    && cost="N/A"
  [ -z "$benefit" ] && benefit="Unknown"

  # Count tasks
  total_tasks=$(count_tasks "$proj_dir")
  done_tasks=$(count_done_tasks "$proj_dir")

  # Build the entry line
  line="- [**${title}**](projects/${folder_name}/index.md) — ${status} | Cost: ${cost} | Benefit: **${benefit}**"

  if [ -n "$owner" ]; then
    line="${line} | Owner: **${owner}**"
  fi

  if [ -n "$special_award" ]; then
    line="${line} | Award: ${special_award}"
  fi

  if [ "$total_tasks" -gt 0 ]; then
    line="${line} | Tasks: ${done_tasks}/${total_tasks} done"
  fi

  if [ "$status" = "Won't Do" ]; then
    wontdo_lines="${wontdo_lines}${line}"$'\n'
  else
    normal_lines="${normal_lines}${line}"$'\n'
  fi

  project_count=$((project_count + 1))
done

echo "Found $project_count project(s)."

# ──────────────────────────────────────────────
# Build replacement block
# ──────────────────────────────────────────────
new_block="<!-- PROJECT_LIST_START -->"$'\n'

if [ -n "$normal_lines" ]; then
  new_block="${new_block}${normal_lines}"
else
  new_block="${new_block}"$'\n'
fi

if [ -n "$wontdo_lines" ]; then
  new_block="${new_block}"$'\n'
  new_block="${new_block}<details>"$'\n'
  new_block="${new_block}<summary>Won't Do</summary>"$'\n'
  new_block="${new_block}"$'\n'
  new_block="${new_block}${wontdo_lines}"
  new_block="${new_block}"$'\n'
  new_block="${new_block}</details>"$'\n'
fi

new_block="${new_block}<!-- PROJECT_LIST_END -->"

# ──────────────────────────────────────────────
# Replace markers in index.md using awk
# ──────────────────────────────────────────────
echo "Updating $INDEX_FILE ..."

awk -v new_block="$new_block" '
  /<!-- PROJECT_LIST_START -->/ {
    print new_block
    skip = 1
    next
  }
  /<!-- PROJECT_LIST_END -->/ {
    skip = 0
    next
  }
  !skip { print }
' "$INDEX_FILE" > "${INDEX_FILE}.tmp"

mv "${INDEX_FILE}.tmp" "$INDEX_FILE"

echo "Done. $INDEX_FILE updated."
