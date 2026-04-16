#!/bin/bash
# test-all-fixtures.sh — Mass test: generate + validate all fixtures × all styles
# Usage: bash scripts/test-all-fixtures.sh [fixtures-dir]
#
# Defaults to .agents-output/diagram/tmp/ for fixtures.
# Generates into .agents-output/diagram/svg/test-run-*/

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
FIXTURES_DIR="${1:-$PROJECT_ROOT/.agents-output/diagram/tmp}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUT_DIR="$PROJECT_ROOT/.agents-output/diagram/svg/test-run-${TIMESTAMP}"

STYLES="flat-icon dark-terminal blueprint notion-clean glassmorphism claude-official openai-official"

# Use python or python3
PYTHON="python"
if ! "$PYTHON" -c "import sys" 2>/dev/null; then
    PYTHON="python3"
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Find fixtures
FIXTURE_FILES=$(find "$FIXTURES_DIR" -name "*.json" -type f 2>/dev/null | sort)
FIXTURE_COUNT=$(echo "$FIXTURE_FILES" | grep -c . || true)

if [ "$FIXTURE_COUNT" -eq 0 ]; then
    echo -e "${RED}No JSON fixtures found in $FIXTURES_DIR${NC}"
    exit 1
fi

mkdir -p "$OUT_DIR"
echo -e "${CYAN}=== SVG Generator Test Suite ===${NC}"
echo "Fixtures:  $FIXTURE_COUNT"
echo "Styles:    7"
echo "Total:     $((FIXTURE_COUNT * 7)) SVGs"
echo "Output:    $OUT_DIR"
echo "----------------------------------------"

PASS_GEN=0
FAIL_GEN=0
PASS_VAL=0
FAIL_VAL=0
FAILURES=""

for fixture_path in $FIXTURE_FILES; do
    fixture=$(basename "$fixture_path" .json)
    for sty in $STYLES; do
        outname="${fixture}-${sty}.svg"
        outpath="$OUT_DIR/$outname"

        # Generate
        if $PYTHON "$SCRIPT_DIR/svg-gen.py" -i "$fixture_path" -o "$outpath" --style "$sty" --output-dir "$OUT_DIR" >/dev/null 2>&1; then
            PASS_GEN=$((PASS_GEN + 1))

            # Validate (use the actual output path which may differ due to --output-dir)
            actual_path="$OUT_DIR/$outname"
            if [ ! -f "$actual_path" ]; then
                actual_path=$(ls -t "$OUT_DIR"/${fixture}*${sty}*.svg 2>/dev/null | head -1)
            fi

            if [ -f "$actual_path" ]; then
                VAL_RESULT=$(bash "$SCRIPT_DIR/validate-svg.sh" "$actual_path" 2>&1 | sed 's/\x1b\[[0-9;]*m//g' | tail -1)
                if echo "$VAL_RESULT" | grep -q "passed"; then
                    PASS_VAL=$((PASS_VAL + 1))
                else
                    FAIL_VAL=$((FAIL_VAL + 1))
                    FAILURES="${FAILURES}\n  VAL-FAIL: ${outname}"
                fi
            fi
        else
            FAIL_GEN=$((FAIL_GEN + 1))
            FAILURES="${FAILURES}\n  GEN-FAIL: ${outname}"
        fi
    done
done

TOTAL=$((PASS_GEN + FAIL_GEN))
echo ""
echo "----------------------------------------"
echo -e "${CYAN}=== RESULTS ===${NC}"
echo -e "Generation: ${GREEN}${PASS_GEN}${NC} pass, ${RED}${FAIL_GEN}${NC} fail / ${TOTAL} total"
echo -e "Validation: ${GREEN}${PASS_VAL}${NC} pass, ${RED}${FAIL_VAL}${NC} fail / ${PASS_GEN} generated"

if [ -n "$FAILURES" ]; then
    echo -e "\n${RED}Failures:${NC}${FAILURES}"
fi

if [ "$FAIL_GEN" -eq 0 ] && [ "$FAIL_VAL" -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed.${NC}"
    exit 1
fi
