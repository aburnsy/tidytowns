#!/bin/bash
# generate-my-tasks.sh - Rebuild the tasks table in site/docs/my-tasks.md
# Scans all task-*.md files (not templates) across all project folders.
# Replaces content between <!-- TASKS_START --> and <!-- TASKS_END --> markers.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_DIR="$SCRIPT_DIR/../site/docs/projects"
TASKS_FILE="$SCRIPT_DIR/../site/docs/my-tasks.md"

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
# Helper: read assignees list from frontmatter
# Returns comma-separated list
# ──────────────────────────────────────────────
read_assignees() {
  local file="$1"
  # Extract the assignees block: lines after "assignees:" that start with "  - "
  awk '
    /^assignees:/{found=1; next}
    found && /^  - /{
      gsub(/^  - /, "")
      gsub(/^"/, ""); gsub(/"$/, "")
      if (NR > 1 && result != "") result = result ", "
      result = result $0
    }
    found && /^[^ ]/{exit}
    END{print result}
  ' "$file"
}

# ──────────────────────────────────────────────
# Scan task files
# ──────────────────────────────────────────────
echo "Scanning tasks in $PROJECTS_DIR ..."

table_rows=""
task_count=0

for proj_dir in "$PROJECTS_DIR"/[0-9][0-9][0-9]-*/; do
  [ -d "$proj_dir" ] || continue

  folder_name="$(basename "$proj_dir")"
  proj_index="$proj_dir/index.md"

  # Get project title
  proj_title=""
  if [ -f "$proj_index" ]; then
    proj_title=$(read_field "$proj_index" "title")
  fi
  [ -z "$proj_title" ] && proj_title="$folder_name"

  for task_file in "$proj_dir"task-*.md; do
    [ -f "$task_file" ] || continue

    # Skip template files
    case "$task_file" in *-template.md) continue ;; esac

    task_filename="$(basename "$task_file")"

    status=$(read_field "$task_file" "status")
    title=$(read_field "$task_file" "title")
    due_date=$(read_field "$task_file" "due_date")
    assignees=$(read_assignees "$task_file")

    # Skip done tasks
    [ "$status" = "done" ] && continue

    echo "  $folder_name / $task_filename  [$status]"

    # Defaults
    [ -z "$title" ]     && title="$task_filename"
    [ -z "$status" ]    && status="pending"
    [ -z "$due_date" ]  && due_date="—"
    [ -z "$assignees" ] && assignees="—"

    # Build task link relative to my-tasks.md (which is in docs/)
    task_link="projects/${folder_name}/${task_filename}"

    row="| [${title}](${task_link}) | ${proj_title} | ${status} | ${due_date} | ${assignees} |"
    table_rows="${table_rows}${row}"$'\n'
    task_count=$((task_count + 1))
  done
done

echo "Found $task_count open task(s)."

# ──────────────────────────────────────────────
# Build replacement block
# ──────────────────────────────────────────────
new_block="<!-- TASKS_START -->"$'\n'

if [ "$task_count" -gt 0 ]; then
  new_block="${new_block}"$'\n'
  new_block="${new_block}| Task | Project | Status | Due Date | Assigned To |"$'\n'
  new_block="${new_block}|------|---------|--------|----------|-------------|"$'\n'
  new_block="${new_block}${table_rows}"
else
  new_block="${new_block}"$'\n'
  new_block="${new_block}*No open tasks found.*"$'\n'
fi

new_block="${new_block}<!-- TASKS_END -->"

# ──────────────────────────────────────────────
# Replace markers in my-tasks.md using awk
# ──────────────────────────────────────────────
echo "Updating $TASKS_FILE ..."

awk -v new_block="$new_block" '
  /<!-- TASKS_START -->/ {
    print new_block
    skip = 1
    next
  }
  /<!-- TASKS_END -->/ {
    skip = 0
    next
  }
  !skip { print }
' "$TASKS_FILE" > "${TASKS_FILE}.tmp"

mv "${TASKS_FILE}.tmp" "$TASKS_FILE"

echo "Done. $TASKS_FILE updated."
