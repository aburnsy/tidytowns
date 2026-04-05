#!/bin/bash
# new-task.sh - Interactive script to create a task within a TidyTowns project
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_DIR="$SCRIPT_DIR/../site/docs/projects"

# ──────────────────────────────────────────────
# 1. List existing projects
# ──────────────────────────────────────────────
echo ""
echo "============================================"
echo "  New TidyTowns Task"
echo "============================================"
echo ""
echo "Available projects:"
echo ""

declare -a PROJECT_DIRS
declare -a PROJECT_NUMS
idx=1

for dir in "$PROJECTS_DIR"/[0-9][0-9][0-9]-*/; do
  [ -d "$dir" ] || continue
  base="$(basename "$dir")"
  num="${base%%\-*}"

  # Extract title from frontmatter
  proj_title=""
  if [ -f "$dir/index.md" ]; then
    proj_title=$(grep -m1 '^title:' "$dir/index.md" | sed 's/^title: *//;s/^"//;s/"$//')
  fi
  [ -z "$proj_title" ] && proj_title="$base"

  printf "  %3d) [%s] %s\n" "$idx" "$num" "$proj_title"
  PROJECT_DIRS[$idx]="$dir"
  PROJECT_NUMS[$idx]="$num"
  idx=$((idx + 1))
done

if [ ${#PROJECT_DIRS[@]} -eq 0 ]; then
  echo "No projects found in $PROJECTS_DIR" >&2
  exit 1
fi

echo ""
read -rp "Select project number: " proj_choice

if ! [[ "$proj_choice" =~ ^[0-9]+$ ]] || [ -z "${PROJECT_DIRS[$proj_choice]+x}" ]; then
  echo "Invalid selection." >&2
  exit 1
fi

selected_dir="${PROJECT_DIRS[$proj_choice]}"
selected_base="$(basename "$selected_dir")"

echo "Selected: $selected_base"

# Read tags from parent project index.md
parent_tags_yaml=""
if [ -f "$selected_dir/index.md" ]; then
  # Extract tags block from YAML frontmatter (lines between tags: and next key)
  parent_tags_yaml=$(awk '/^tags:/{found=1; next} found && /^  - /{print} found && /^[^ ]/{exit}' "$selected_dir/index.md")
fi

# ──────────────────────────────────────────────
# 2. Task title
# ──────────────────────────────────────────────
echo ""
read -rp "Task title: " task_title
if [ -z "$task_title" ]; then
  echo "Error: task title is required." >&2
  exit 1
fi

# Build slug from title
task_slug=$(echo "$task_title" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//')

# ──────────────────────────────────────────────
# 3. One-off or recurring?
# ──────────────────────────────────────────────
echo ""
echo "Task type:"
echo "  1) One-off"
echo "  2) Recurring"
read -rp "Type [1]: " task_type_num

is_recurring=false
if [ "${task_type_num:-1}" = "2" ]; then
  is_recurring=true
fi

frequency=""
active_months=""
due_date=""

if $is_recurring; then
  echo ""
  echo "Frequency:"
  echo "  1) weekly"
  echo "  2) bi-monthly"
  echo "  3) monthly"
  echo "  4) seasonal"
  read -rp "Frequency [3]: " freq_num
  case "${freq_num:-3}" in
    1) frequency="weekly" ;;
    2) frequency="bi-monthly" ;;
    4) frequency="seasonal" ;;
    *) frequency="monthly" ;;
  esac

  echo ""
  echo "Active months (e.g. Apr-Sep or Year-round) [Year-round]:"
  read -rp "Active months: " active_months
  active_months="${active_months:-Year-round}"
else
  read -rp "Due date (YYYY-MM-DD or blank): " due_date
fi

# ──────────────────────────────────────────────
# 4. Assignee
# ──────────────────────────────────────────────
echo ""
read -rp "Assignee shortname (or blank): " assignee

# ──────────────────────────────────────────────
# 5. Description
# ──────────────────────────────────────────────
echo ""
read -rp "Description (single line): " description

# ──────────────────────────────────────────────
# 6. Build the task file
# ──────────────────────────────────────────────
if $is_recurring; then
  task_filename="task-${task_slug}-template.md"
  task_status="template"
else
  task_filename="task-${task_slug}.md"
  task_status="pending"
fi

task_file="$selected_dir/$task_filename"

if [ -f "$task_file" ]; then
  echo "Error: task file already exists: $task_file" >&2
  exit 1
fi

# Build tags YAML block (reuse parent tags)
tags_block=""
if [ -n "$parent_tags_yaml" ]; then
  tags_block="tags:"$'\n'"$parent_tags_yaml"
else
  tags_block="tags: []"
fi

# Build optional frontmatter lines
due_date_line=""
if [ -n "$due_date" ]; then
  due_date_line="due_date: \"$due_date\""$'\n'
fi

recurring_line="recurring: false"
if $is_recurring; then
  recurring_line="recurring: \"$frequency\""
fi

active_months_line=""
if [ -n "$active_months" ]; then
  active_months_line="active_months: \"$active_months\""$'\n'
fi

cat > "$task_file" <<MDEOF
---
title: "$task_title"
status: "$task_status"
assignee: "$assignee"
${due_date_line}${recurring_line}
${active_months_line}${tags_block}
---

${description:-*No description provided yet.*}
MDEOF

echo ""
echo "Created: $task_file"
