#!/usr/bin/env bash
set -euo pipefail

# blast-radius.sh — trace callers and dependents of changed files
# Usage: ./scripts/blast-radius.sh [file1 file2 ...]
#        With no args, uses `git diff --name-only HEAD~1..HEAD`

# ---------------------------------------------------------------------------
# 1. Determine changed files
# ---------------------------------------------------------------------------

declare -a CHANGED_FILES=()

if [[ $# -gt 0 ]]; then
  for f in "$@"; do
    CHANGED_FILES+=("$f")
  done
else
  # Try HEAD~1..HEAD first; fall back to --cached
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
  echo "No changed files detected."
  exit 0
fi

# ---------------------------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------------------------

SOURCE_EXTS="-o -name '*.ts' -o -name '*.js' -o -name '*.py' -o -name '*.go' -o -name '*.rs' -o -name '*.java' -o -name '*.rb'"
SKIP_DIRS="node_modules|\.git|dist|build"

# grep_refs FILE_BASENAME — print files that import/require/reference the basename
grep_refs() {
  local base="$1"
  # Strip extension for a cleaner search token (e.g. "auth.ts" → "auth")
  local token
  token="$(basename "$base")"
  # Remove leading dot-segment if path like ./foo/bar
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

# is_test_file FILE — returns 0 if file looks like a test
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
    # Exclude the changed file itself
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
# 4. Trace transitive dependents (1 level deeper from direct callers)
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
      # Avoid duplicates
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

# Also scan direct callers for test files
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

# Check filenames of changed files
for cf in "${CHANGED_FILES[@]}"; do
  if echo "$cf" | grep -qiE "$HIGH_RISK_PATTERN"; then
    is_high_risk=true
    break
  fi
done

# Check content of changed files (only files that exist on disk)
if [[ "$is_high_risk" == false ]]; then
  for cf in "${CHANGED_FILES[@]}"; do
    if [[ -f "$cf" ]] && grep -qiE "$HIGH_RISK_PATTERN" "$cf" 2>/dev/null; then
      is_high_risk=true
      break
    fi
  done
fi

# Blast radius = direct callers + transitive dependents
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

# No test coverage elevates LOW → MEDIUM
if [[ "$RISK_LEVEL" == "LOW" && ${#AFFECTED_TESTS[@]} -eq 0 ]]; then
  RISK_LEVEL="MEDIUM"
fi

# ---------------------------------------------------------------------------
# 7. Output formatted report
# ---------------------------------------------------------------------------

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

# Priority: CHANGED → CALLER → TEST → TRANSITIVE
for f in "${CHANGED_FILES[@]}"; do
  echo "  1-CHANGED    $f"
done
for f in "${DIRECT_CALLERS[@]}"; do
  echo "  2-CALLER     $f"
done
for f in "${AFFECTED_TESTS[@]}"; do
  echo "  3-TEST       $f"
done
for f in "${TRANSITIVE_DEPENDENTS[@]}"; do
  echo "  4-TRANSITIVE $f"
done

echo ""
echo "============================================================"
