#!/usr/bin/env bash
set -euo pipefail

# hub-detect.sh — finds most-connected files (hubs) and bridge nodes in a codebase

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-$(dirname "$SCRIPT_DIR")}"

echo "=== HUB DETECTION: $TARGET_DIR ==="
echo ""

# Step 1: Find all source files (excluding node_modules, .git, dist, build)
mapfile -t SOURCE_FILES < <(
  find "$TARGET_DIR" \
    -type f \
    \( -name "*.ts" -o -name "*.js" -o -name "*.py" -o -name "*.go" \
       -o -name "*.rs" -o -name "*.java" -o -name "*.rb" \) \
    ! -path "*/node_modules/*" \
    ! -path "*/.git/*" \
    ! -path "*/dist/*" \
    ! -path "*/build/*" \
    2>/dev/null | sort
)

TOTAL="${#SOURCE_FILES[@]}"

if [[ "$TOTAL" -eq 0 ]]; then
  echo "No source files found."
  exit 0
fi

echo "Scanning $TOTAL source files..."
echo ""

# Step 2: For each source file, count how many OTHER files import/require/reference it
declare -A IMPORT_COUNT
declare -A IMPORTER_DIRS

for file in "${SOURCE_FILES[@]}"; do
  # Get basename without extension
  base="$(basename "$file")"
  base_no_ext="${base%.*}"

  count=0
  declare -A seen_dirs=()

  for other in "${SOURCE_FILES[@]}"; do
    # Skip self
    [[ "$file" == "$other" ]] && continue

    # Check if other file references this file's basename (import/require/reference patterns)
    if grep -qE "(import|require|from|use|include|load)[^'\"\`]*['\"\`][^'\"\`]*\b${base_no_ext}\b" "$other" 2>/dev/null; then
      (( count++ )) || true
      other_dir="$(dirname "$other")"
      seen_dirs["$other_dir"]=1
    fi
  done

  if [[ "$count" -gt 0 ]]; then
    IMPORT_COUNT["$file"]="$count"
    IMPORTER_DIRS["$file"]="${!seen_dirs[*]}"
  fi

  unset seen_dirs
done

# Step 3: Sort by count, display top 10 as hubs
echo "--- TOP HUBS (most imported files) ---"

# Build sorted list
sorted_hubs=()
for file in "${!IMPORT_COUNT[@]}"; do
  sorted_hubs+=("${IMPORT_COUNT[$file]} $file")
done

if [[ "${#sorted_hubs[@]}" -eq 0 ]]; then
  echo "  (no files with importers found)"
else
  # Sort numerically descending, take top 10
  while IFS=' ' read -r cnt fpath; do
    base="$(basename "$fpath")"
    if [[ "$cnt" -ge 20 ]]; then
      label="CRITICAL HUB"
    elif [[ "$cnt" -ge 10 ]]; then
      label="MAJOR HUB"
    else
      label="hub"
    fi
    echo "  [$label] $base — imported by $cnt files"
  done < <(printf '%s\n' "${sorted_hubs[@]}" | sort -rn | head -10)
fi

echo ""

# Step 4: Bridge detection — files whose importers come from 2+ different directories
echo "--- BRIDGE NODES (cross-directory connectors) ---"

bridges_found=0
for file in "${!IMPORTER_DIRS[@]}"; do
  dir_list="${IMPORTER_DIRS[$file]}"
  # Count distinct directories
  num_dirs=$(echo "$dir_list" | tr ' ' '\n' | grep -c . || true)

  if [[ "$num_dirs" -ge 2 ]]; then
    base="$(basename "$file")"
    echo "  [BRIDGE] $base — connects $num_dirs directories"
    (( bridges_found++ )) || true
  fi
done

if [[ "$bridges_found" -eq 0 ]]; then
  echo "  (no bridge nodes detected)"
fi

echo ""

# Step 5: Output summary
FILES_WITH_IMPORTERS="${#IMPORT_COUNT[@]}"

echo "=== SUMMARY ==="
echo "  Total source files: $TOTAL"
echo "  Files with importers: $FILES_WITH_IMPORTERS"
