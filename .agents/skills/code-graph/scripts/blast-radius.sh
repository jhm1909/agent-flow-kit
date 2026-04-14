#!/usr/bin/env bash
set -euo pipefail

# blast-radius.sh — trace callers and dependents of changed files
# Usage: scripts/blast-radius.sh [--json] [file1 file2 ...]
#   --json    Output JSON for agent consumption
#   files     Changed files to analyze (default: auto-detect from git diff)

# ---------------------------------------------------------------------------
# Parse flags
# ---------------------------------------------------------------------------

JSON_MODE=false
declare -a CHANGED_FILES=()

for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    --help|-h)
      echo "Usage: blast-radius.sh [--json] [file1 file2 ...]"
      echo ""
      echo "Trace callers, dependents, and tests for changed files."
      echo "Outputs risk classification: CRITICAL / HIGH / MEDIUM / LOW."
      echo ""
      echo "Options:"
      echo "  --json    Output JSON for agent consumption or piping"
      echo "  files     Changed files (default: auto-detect from git diff)"
      echo ""
      echo "Examples:"
      echo "  blast-radius.sh                    # Auto-detect, text output"
      echo "  blast-radius.sh --json             # Auto-detect, JSON output"
      echo "  blast-radius.sh src/auth.py        # Specific file, text output"
      echo "  blast-radius.sh --json src/auth.py src/middleware.py"
      exit 0
      ;;
    *) CHANGED_FILES+=("$arg") ;;
  esac
done

# ---------------------------------------------------------------------------
# 1. Determine changed files
# ---------------------------------------------------------------------------

if [[ ${#CHANGED_FILES[@]} -eq 0 ]]; then
  if git diff --name-only HEAD~1..HEAD &>/dev/null && \
     mapfile -t _tmp < <(git diff --name-only HEAD~1..HEAD 2>/dev/null) && \
     [[ ${#_tmp[@]} -gt 0 ]]; then
    CHANGED_FILES=("${_tmp[@]}")
  elif mapfile -t _tmp < <(git diff --name-only --cached 2>/dev/null) && \
       [[ ${#_tmp[@]} -gt 0 ]]; then
    CHANGED_FILES=("${_tmp[@]}")
  fi
fi

if [[ ${#CHANGED_FILES[@]} -eq 0 ]]; then
  if [[ "$JSON_MODE" == true ]]; then
    echo '{"changed":[],"callers":[],"transitive":[],"tests":[],"risk":{"level":"NONE","blast_radius":0,"high_risk_change":false}}'
  else
    echo "No changed files detected."
  fi
  exit 0
fi

# ---------------------------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------------------------

grep_refs() {
  local base="$1"
  local token
  token="$(basename "$base")"
  local stem="${token%.*}"

  grep -rl \
    --include="*.ts" --include="*.js" \
    --include="*.py" --include="*.go" \
    --include="*.rs" --include="*.java" \
    --include="*.rb" \
    --exclude-dir="node_modules" \
    --exclude-dir=".git" \
    --exclude-dir="dist" \
    --exclude-dir="build" \
    -e "$stem" \
    . 2>/dev/null || true
}

is_test_file() {
  local f="$1"
  [[ "$f" =~ \.(test|spec)\. ]] || \
  [[ "$(basename "$f")" =~ ^test_ ]] || \
  [[ "$(basename "$f")" =~ _test\. ]]
}

# ---------------------------------------------------------------------------
# 3. Trace direct callers
# ---------------------------------------------------------------------------

declare -A SEEN_CALLERS=()
declare -a DIRECT_CALLERS=()

for cf in "${CHANGED_FILES[@]}"; do
  while IFS= read -r caller; do
    real_caller="${caller#./}"
    if [[ -n "$real_caller" ]] && \
       [[ ! " ${CHANGED_FILES[*]} " =~ " ${real_caller} " ]] && \
       [[ -z "${SEEN_CALLERS[$real_caller]+x}" ]]; then
      SEEN_CALLERS["$real_caller"]=1
      DIRECT_CALLERS+=("$real_caller")
    fi
  done < <(grep_refs "$cf")
done

# ---------------------------------------------------------------------------
# 4. Trace transitive dependents (1 level deeper)
# ---------------------------------------------------------------------------

declare -A SEEN_TRANSITIVE=()
declare -a TRANSITIVE_DEPENDENTS=()

for caller in "${DIRECT_CALLERS[@]}"; do
  while IFS= read -r dep; do
    real_dep="${dep#./}"
    if [[ -n "$real_dep" ]] && \
       [[ ! " ${CHANGED_FILES[*]} " =~ " ${real_dep} " ]] && \
       [[ -z "${SEEN_CALLERS[$real_dep]+x}" ]] && \
       [[ -z "${SEEN_TRANSITIVE[$real_dep]+x}" ]]; then
      SEEN_TRANSITIVE["$real_dep"]=1
      TRANSITIVE_DEPENDENTS+=("$real_dep")
    fi
  done < <(grep_refs "$caller")
done

# ---------------------------------------------------------------------------
# 5. Find affected tests
# ---------------------------------------------------------------------------

declare -a AFFECTED_TESTS=()

for cf in "${CHANGED_FILES[@]}"; do
  stem="$(basename "${cf%.*}")"
  while IFS= read -r tf; do
    real_tf="${tf#./}"
    if is_test_file "$real_tf"; then
      if [[ ! " ${AFFECTED_TESTS[*]} " =~ " ${real_tf} " ]]; then
        AFFECTED_TESTS+=("$real_tf")
      fi
    fi
  done < <(grep -rl \
    --include="*.ts" --include="*.js" \
    --include="*.py" --include="*.go" \
    --include="*.rs" --include="*.java" \
    --include="*.rb" \
    --exclude-dir="node_modules" \
    --exclude-dir=".git" \
    --exclude-dir="dist" \
    --exclude-dir="build" \
    -e "$stem" \
    . 2>/dev/null || true)
done

for caller in "${DIRECT_CALLERS[@]}"; do
  if is_test_file "$caller"; then
    if [[ ! " ${AFFECTED_TESTS[*]} " =~ " ${caller} " ]]; then
      AFFECTED_TESTS+=("$caller")
    fi
  fi
done

# ---------------------------------------------------------------------------
# 6. Risk classification
# ---------------------------------------------------------------------------

HIGH_RISK_PATTERN="auth|crypto|password|token|secret|validation|permission|access"

is_high_risk=false

for cf in "${CHANGED_FILES[@]}"; do
  if echo "$cf" | grep -qiE "$HIGH_RISK_PATTERN"; then
    is_high_risk=true
    break
  fi
done

if [[ "$is_high_risk" == false ]]; then
  for cf in "${CHANGED_FILES[@]}"; do
    if [[ -f "$cf" ]] && grep -qiE "$HIGH_RISK_PATTERN" "$cf" 2>/dev/null; then
      is_high_risk=true
      break
    fi
  done
fi

blast_radius=$(( ${#DIRECT_CALLERS[@]} + ${#TRANSITIVE_DEPENDENTS[@]} ))

if [[ "$is_high_risk" == true && $blast_radius -gt 50 ]]; then
  RISK_LEVEL="CRITICAL"
elif [[ "$is_high_risk" == true || $blast_radius -gt 50 ]]; then
  RISK_LEVEL="HIGH"
elif [[ $blast_radius -gt 10 ]]; then
  RISK_LEVEL="MEDIUM"
else
  RISK_LEVEL="LOW"
fi

if [[ "$RISK_LEVEL" == "LOW" && ${#AFFECTED_TESTS[@]} -eq 0 ]]; then
  RISK_LEVEL="MEDIUM"
fi

# ---------------------------------------------------------------------------
# 7. Output
# ---------------------------------------------------------------------------

if [[ "$JSON_MODE" == true ]]; then
  # JSON output
  json_array() {
    local arr=("$@")
    local first=true
    echo -n "["
    for item in "${arr[@]}"; do
      if [[ "$first" == true ]]; then first=false; else echo -n ","; fi
      echo -n "\"$item\""
    done
    echo -n "]"
  }

  echo "{"
  echo -n '  "changed": '; json_array "${CHANGED_FILES[@]}"; echo ","
  echo -n '  "callers": '; json_array "${DIRECT_CALLERS[@]}"; echo ","
  echo -n '  "transitive": '; json_array "${TRANSITIVE_DEPENDENTS[@]}"; echo ","
  echo -n '  "tests": '; json_array "${AFFECTED_TESTS[@]}"; echo ","
  echo '  "risk": {'
  echo "    \"level\": \"$RISK_LEVEL\","
  echo "    \"blast_radius\": $blast_radius,"
  echo "    \"high_risk_change\": $is_high_risk,"
  echo "    \"test_coverage\": ${#AFFECTED_TESTS[@]}"
  echo "  },"
  # Priority-ordered review list
  echo '  "review_order": ['
  first=true
  for f in "${CHANGED_FILES[@]}"; do
    if [[ "$first" == true ]]; then first=false; else echo ","; fi
    printf '    {"file":"%s","priority":"changed"}' "$f"
  done
  for f in "${DIRECT_CALLERS[@]}"; do
    echo ","
    printf '    {"file":"%s","priority":"caller"}' "$f"
  done
  for f in "${AFFECTED_TESTS[@]}"; do
    echo ","
    printf '    {"file":"%s","priority":"test"}' "$f"
  done
  for f in "${TRANSITIVE_DEPENDENTS[@]}"; do
    echo ","
    printf '    {"file":"%s","priority":"transitive"}' "$f"
  done
  echo ""
  echo "  ]"
  echo "}"

else
  # Human-readable text output
  echo "============================================================"
  echo "  BLAST RADIUS ANALYSIS REPORT"
  echo "============================================================"
  echo ""

  echo "## Changed Files (${#CHANGED_FILES[@]})"
  for f in "${CHANGED_FILES[@]}"; do
    echo "  [CHANGED] $f"
  done
  echo ""

  echo "## Direct Callers (${#DIRECT_CALLERS[@]})"
  if [[ ${#DIRECT_CALLERS[@]} -eq 0 ]]; then
    echo "  (none)"
  else
    for f in "${DIRECT_CALLERS[@]}"; do
      echo "  [CALLER]  $f"
    done
  fi
  echo ""

  echo "## Transitive Dependents (${#TRANSITIVE_DEPENDENTS[@]})"
  if [[ ${#TRANSITIVE_DEPENDENTS[@]} -eq 0 ]]; then
    echo "  (none)"
  else
    for f in "${TRANSITIVE_DEPENDENTS[@]}"; do
      echo "  [TRANSITIVE] $f"
    done
  fi
  echo ""

  echo "## Affected Tests (${#AFFECTED_TESTS[@]})"
  if [[ ${#AFFECTED_TESTS[@]} -eq 0 ]]; then
    echo "  (none — no test coverage detected)"
  else
    for f in "${AFFECTED_TESTS[@]}"; do
      echo "  [TEST]    $f"
    done
  fi
  echo ""

  echo "## Risk Assessment"
  echo "  Risk Level  : $RISK_LEVEL"
  echo "  Blast Radius: $blast_radius file(s) impacted"
  echo "  High-Risk Change: $is_high_risk"
  echo ""

  echo "## Files to Review (priority order)"
  for f in "${CHANGED_FILES[@]}"; do echo "  1-CHANGED    $f"; done
  for f in "${DIRECT_CALLERS[@]}"; do echo "  2-CALLER     $f"; done
  for f in "${AFFECTED_TESTS[@]}"; do echo "  3-TEST       $f"; done
  for f in "${TRANSITIVE_DEPENDENTS[@]}"; do echo "  4-TRANSITIVE $f"; done

  echo ""
  echo "============================================================"
fi
