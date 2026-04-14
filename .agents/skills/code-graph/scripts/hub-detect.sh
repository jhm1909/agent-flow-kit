#!/usr/bin/env bash
set -eo pipefail

# hub-detect.sh — find most-connected files (hubs) and bridge nodes
# Usage: scripts/hub-detect.sh [--json] [directory]
#   --json    Output JSON (pipeable to svg-gen.py)
#   directory Target directory (default: project root)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Parse flags
JSON_MODE=false
TARGET_DIR="$PROJECT_ROOT"

for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    --help|-h)
      echo "Usage: hub-detect.sh [--json] [directory]"
      echo ""
      echo "Find most-connected files (hubs) and cross-directory connectors (bridges)."
      echo ""
      echo "Options:"
      echo "  --json    Output JSON for piping to svg-gen.py or agent consumption"
      echo "  directory Target directory (default: project root)"
      echo ""
      echo "Examples:"
      echo "  hub-detect.sh                    # Text output"
      echo "  hub-detect.sh --json             # JSON output"
      echo "  hub-detect.sh --json src/        # JSON for specific directory"
      echo "  hub-detect.sh --json | python3 skills/diagram/scripts/svg-gen.py -o arch.svg --style blueprint"
      exit 0
      ;;
    *) TARGET_DIR="$arg" ;;
  esac
done

# ---------------------------------------------------------------------------
# 1. Find source files
# ---------------------------------------------------------------------------

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
  if [[ "$JSON_MODE" == true ]]; then
    echo '{"nodes":[],"edges":[],"summary":{"total_files":0,"hubs":0,"bridges":0}}'
  else
    echo "No source files found."
  fi
  exit 0
fi

# ---------------------------------------------------------------------------
# 2. Count imports per file
# ---------------------------------------------------------------------------

declare -A IMPORT_COUNT
declare -A IMPORTER_DIRS
declare -A IMPORTERS  # track who imports whom

for file in "${SOURCE_FILES[@]}"; do
  base="$(basename "$file")"
  base_no_ext="${base%.*}"

  count=0
  declare -A seen_dirs=()
  importers_list=""

  for other in "${SOURCE_FILES[@]}"; do
    [[ "$file" == "$other" ]] && continue
    if grep -qE "(import|require|from)\s+.*\b${base_no_ext}\b|['\"\`].*\b${base_no_ext}\b" "$other" 2>/dev/null; then
      (( count++ )) || true
      other_dir="$(dirname "$other")"
      seen_dirs["$other_dir"]=1
      importers_list="${importers_list}${other},"
    fi
  done

  if [[ "$count" -gt 0 ]]; then
    IMPORT_COUNT["$file"]="$count"
    IMPORTER_DIRS["$file"]="${!seen_dirs[*]}"
    IMPORTERS["$file"]="$importers_list"
  fi

  unset seen_dirs
done

# ---------------------------------------------------------------------------
# 3. Build sorted hub list
# ---------------------------------------------------------------------------

sorted_hubs=()
for file in "${!IMPORT_COUNT[@]}"; do
  sorted_hubs+=("${IMPORT_COUNT[$file]} $file")
done

# ---------------------------------------------------------------------------
# 4. Detect bridges
# ---------------------------------------------------------------------------

declare -A BRIDGE_MAP  # file -> num_dirs

for file in "${!IMPORTER_DIRS[@]}"; do
  dir_list="${IMPORTER_DIRS[$file]}"
  num_dirs=$(echo "$dir_list" | tr ' ' '\n' | grep -c . || true)
  if [[ "$num_dirs" -ge 2 ]]; then
    BRIDGE_MAP["$file"]="$num_dirs"
  fi
done

# ---------------------------------------------------------------------------
# 5. Output
# ---------------------------------------------------------------------------

if [[ "$JSON_MODE" == true ]]; then
  # JSON output — compatible with svg-gen.py input format
  echo "{"
  echo '  "title": "Architecture: '"$(basename "$TARGET_DIR")"'",'

  # Nodes
  echo '  "nodes": ['
  layer=0
  first=true
  while IFS=' ' read -r cnt fpath; do
    [[ -z "$fpath" ]] && continue
    rel="${fpath#$TARGET_DIR/}"
    base="$(basename "$fpath")"
    id="${base%.*}"

    # Determine shape
    shape="rect"
    bridge_check="${BRIDGE_MAP["$fpath"]:-}"
    if [[ -n "$bridge_check" ]]; then
      shape="hexagon"
    fi
    if [[ "$cnt" -ge 20 ]]; then
      shape="llm"  # double-border = critical hub
    fi

    if [[ "$first" == true ]]; then first=false; else echo ","; fi
    printf '    {"id":"%s","label":"%s (%s)","shape":"%s","layer":%d}' \
      "$id" "$base" "$cnt" "$shape" "$((layer / 3))"
    (( layer++ )) || true
  done < <(printf '%s\n' "${sorted_hubs[@]}" | sort -rn | head -15)
  echo ""
  echo "  ],"

  # Edges — from importers to hubs
  echo '  "edges": ['
  first=true
  while IFS=' ' read -r cnt fpath; do
    [[ -z "$fpath" ]] && continue
    base="$(basename "$fpath")"
    hub_id="${base%.*}"
    importer_list="${IMPORTERS["$fpath"]:-}"

    IFS=',' read -ra imps <<< "$importer_list"
    for imp in "${imps[@]}"; do
      [[ -z "$imp" ]] && continue
      imp_base="$(basename "$imp")"
      imp_id="${imp_base%.*}"

      # Only add edge if importer is also in our node list (top 15)
      for node_entry in "${sorted_hubs[@]}"; do
        node_path="${node_entry#* }"
        if [[ "$node_path" == "$imp" ]]; then
          edge_type="primary"
          imp_dir="$(dirname "$imp")"
          hub_dir="$(dirname "$fpath")"
          if [[ "$imp_dir" != "$hub_dir" ]]; then
            edge_type="async"  # cross-directory = async style
          fi

          if [[ "$first" == true ]]; then first=false; else echo ","; fi
          printf '    {"from":"%s","to":"%s","type":"%s"}' "$imp_id" "$hub_id" "$edge_type"
          break
        fi
      done
    done
  done < <(printf '%s\n' "${sorted_hubs[@]}" | sort -rn | head -15)
  echo ""
  echo "  ],"

  # Summary
  hub_count=0
  bridge_count=0
  for _k in "${!BRIDGE_MAP[@]}"; do (( bridge_count++ )) || true; done
  while IFS=' ' read -r cnt fpath; do
    (( hub_count++ )) || true
  done < <(printf '%s\n' "${sorted_hubs[@]}" | sort -rn | head -10)

  echo '  "summary": {'
  echo "    \"total_files\": $TOTAL,"
  echo "    \"hubs\": $hub_count,"
  echo "    \"bridges\": $bridge_count"
  echo "  }"
  echo "}"

else
  # Human-readable text output
  echo "=== HUB DETECTION: $TARGET_DIR ==="
  echo ""
  echo "Scanning $TOTAL source files..."
  echo ""

  echo "--- TOP HUBS (most imported files) ---"
  if [[ "${#sorted_hubs[@]}" -eq 0 ]]; then
    echo "  (no files with importers found)"
  else
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
  echo "--- BRIDGE NODES (cross-directory connectors) ---"

  bridges_found=0
  for file in "${!BRIDGE_MAP[@]}"; do
    base="$(basename "$file")"
    num_dirs="${BRIDGE_MAP[$file]}"
    echo "  [BRIDGE] $base — connects $num_dirs directories"
    (( bridges_found++ )) || true
  done

  if [[ "$bridges_found" -eq 0 ]]; then
    echo "  (no bridge nodes detected)"
  fi

  echo ""
  echo "=== SUMMARY ==="
  echo "  Total source files: $TOTAL"
  echo "  Files with importers: ${#IMPORT_COUNT[@]}"
fi
