#!/bin/bash
# generate-recurring.sh - Generate concrete dated task files from recurring templates
# Usage: generate-recurring.sh [months_ahead]
#   months_ahead: number of months to generate (default: 3)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_DIR="$SCRIPT_DIR/../site/docs/projects"

MONTHS_AHEAD="${1:-3}"

# ──────────────────────────────────────────────
# Date helpers (portable, no GNU date -d required)
# ──────────────────────────────────────────────

# Returns "YYYY MM" for a month offset from today
# $1 = offset in months (0 = current month)
month_offset() {
  local offset=$1
  # Use python via uv if available, otherwise fall back to bash arithmetic
  local cur_year cur_mon
  cur_year=$(date +%Y)
  cur_mon=$(date +%-m 2>/dev/null || date +%m | sed 's/^0//')

  local total=$(( (cur_year * 12 + cur_mon - 1) + offset ))
  local year=$(( total / 12 ))
  local mon=$(( total % 12 + 1 ))
  printf "%04d %02d" "$year" "$mon"
}

# Last day of a month: $1=YYYY, $2=MM (zero-padded OK)
last_day_of_month() {
  local year=$1
  local mon=$(( 10#$2 ))
  case $mon in
    1|3|5|7|8|10|12) echo 31 ;;
    4|6|9|11)         echo 30 ;;
    2)
      if (( year % 4 == 0 && (year % 100 != 0 || year % 400 == 0) )); then
        echo 29
      else
        echo 28
      fi
      ;;
  esac
}

# Month name abbreviation from number (1-12)
month_abbr() {
  local mon=$(( 10#$1 ))
  local names=( "" Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec )
  echo "${names[$mon]}"
}

# Month number from abbreviation
month_num_from_abbr() {
  local abbr="$1"
  case "$abbr" in
    Jan) echo 1 ;; Feb) echo 2 ;; Mar) echo 3 ;;  Apr) echo 4 ;;
    May) echo 5 ;; Jun) echo 6 ;; Jul) echo 7 ;;  Aug) echo 8 ;;
    Sep) echo 9 ;; Oct) echo 10 ;; Nov) echo 11 ;; Dec) echo 12 ;;
    *) echo 0 ;;
  esac
}

# Returns 0 (true) if month $1 (1-12) is within active_months range "$2"
# active_months format: "Apr-Sep" or "Year-round"
is_active_month() {
  local mon=$1
  local range="$2"

  if [ "$range" = "Year-round" ] || [ -z "$range" ]; then
    return 0
  fi

  local start_abbr end_abbr
  start_abbr="${range%%-*}"
  end_abbr="${range##*-}"

  local start_num end_num
  start_num=$(month_num_from_abbr "$start_abbr")
  end_num=$(month_num_from_abbr "$end_abbr")

  if [ "$start_num" -eq 0 ] || [ "$end_num" -eq 0 ]; then
    # Unrecognised format - assume active
    return 0
  fi

  if [ "$start_num" -le "$end_num" ]; then
    # Normal range e.g. Apr(4) - Sep(9)
    [ "$mon" -ge "$start_num" ] && [ "$mon" -le "$end_num" ] && return 0
  else
    # Wraps year e.g. Oct(10) - Mar(3)
    [ "$mon" -ge "$start_num" ] || [ "$mon" -le "$end_num" ] && return 0
  fi
  return 1
}

# ──────────────────────────────────────────────
# Bi-monthly tracking: we skip alternate months.
# We define "active" bi-monthly months as those
# where (year*12 + month) is even.
# ──────────────────────────────────────────────
is_bimonthly_active() {
  local year=$1 mon=$2
  local idx=$(( year * 12 + mon ))
  (( idx % 2 == 0 )) && return 0 || return 1
}

# ──────────────────────────────────────────────
# Read a frontmatter field from a markdown file
# $1 = file, $2 = field name
# ──────────────────────────────────────────────
read_frontmatter_field() {
  local file="$1" field="$2"
  # Grab value between the two --- delimiters
  awk "
    /^---/{count++; next}
    count==1 && /^${field}:/{
      sub(/^${field}: */, \"\")
      gsub(/^\"|\"$/, \"\")
      print
      exit
    }
    count>=2{exit}
  " "$file"
}

# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
echo "Scanning for recurring task templates..."
echo "Generating for next $MONTHS_AHEAD month(s)."
echo ""

generated=0
skipped=0

# Find all template files
while IFS= read -r -d '' template_file; do
  proj_dir="$(dirname "$template_file")"
  template_base="$(basename "$template_file")"

  # Strip -template.md to get the base slug portion
  # e.g. task-mow-verges-template.md -> task-mow-verges
  task_base="${template_base%-template.md}"

  # Read recurring frequency and active_months
  frequency=$(read_frontmatter_field "$template_file" "recurring")
  active_months=$(read_frontmatter_field "$template_file" "active_months")

  # Skip if not actually recurring
  if [ "$frequency" = "false" ] || [ -z "$frequency" ]; then
    continue
  fi

  echo "Template: $template_file"
  echo "  frequency=$frequency  active_months=${active_months:-Year-round}"

  for (( offset=0; offset<MONTHS_AHEAD; offset++ )); do
    read -r target_year target_mon <<< "$(month_offset "$offset")"

    mon_int=$(( 10#$target_mon ))

    # Check active_months
    if ! is_active_month "$mon_int" "$active_months"; then
      echo "  Skipping $target_year-$target_mon (outside active months)"
      skipped=$(( skipped + 1 ))
      continue
    fi

    # Check bi-monthly
    if [ "$frequency" = "bi-monthly" ]; then
      if ! is_bimonthly_active "$target_year" "$mon_int"; then
        echo "  Skipping $target_year-$target_mon (bi-monthly: alternate month)"
        skipped=$(( skipped + 1 ))
        continue
      fi
    fi

    # Build output filename
    output_file="$proj_dir/${task_base}-${target_year}-${target_mon}.md"

    if [ -f "$output_file" ]; then
      echo "  Skipping $target_year-$target_mon (file exists)"
      skipped=$(( skipped + 1 ))
      continue
    fi

    # Calculate last day of month for due_date
    last_day=$(last_day_of_month "$target_year" "$target_mon")
    due_date="${target_year}-${target_mon}-$(printf "%02d" "$last_day")"

    # Build the new file: copy template, replace status and add due_date
    # We rewrite the frontmatter fields we need to change.
    # Strategy: read the full template, sed-replace status line, inject due_date.
    {
      in_frontmatter=0
      due_date_written=0
      first_fence=0
      while IFS= read -r line; do
        # Track frontmatter fences
        if [ "$line" = "---" ]; then
          if [ "$first_fence" -eq 0 ]; then
            first_fence=1
            in_frontmatter=1
            echo "$line"
            continue
          elif [ "$in_frontmatter" -eq 1 ]; then
            # Closing fence: inject due_date before it if not yet written
            if [ "$due_date_written" -eq 0 ]; then
              echo "due_date: \"$due_date\""
              due_date_written=1
            fi
            in_frontmatter=0
            echo "$line"
            continue
          fi
        fi

        if [ "$in_frontmatter" -eq 1 ]; then
          # Replace status: template -> pending
          if echo "$line" | grep -q '^status:'; then
            echo 'status: "pending"'
            continue
          fi
          # Replace or skip existing due_date (will add fresh one)
          if echo "$line" | grep -q '^due_date:'; then
            echo "due_date: \"$due_date\""
            due_date_written=1
            continue
          fi
        fi

        echo "$line"
      done < "$template_file"
    } > "$output_file"

    echo "  Created: $(basename "$output_file")  (due $due_date)"
    generated=$(( generated + 1 ))
  done

  echo ""

done < <(find "$PROJECTS_DIR" -name "task-*-template.md" -print0)

echo "Done. Generated: $generated  Skipped: $skipped"
