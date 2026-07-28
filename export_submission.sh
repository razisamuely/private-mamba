#!/usr/bin/env bash
# Export a clean zip for paper submission.
# Usage: bash export_submission.sh [output_name]
#
# Respects .zipignore for exclusions. Run from repo root.

set -euo pipefail

NAME="${1:-private-mamba-submission}"
OUT="${NAME}.zip"
IGNORE_FILE=".zipignore"

if [ ! -f "$IGNORE_FILE" ]; then
    echo "ERROR: $IGNORE_FILE not found in repo root." >&2
    exit 1
fi

# Build exclude flags from .zipignore (skip comments and blank lines)
EXCLUDES=()
while IFS= read -r line; do
    line="${line%%#*}"        # strip inline comments
    line="${line%"${line##*[![:space:]]}"}"  # strip trailing whitespace
    [[ -z "$line" ]] && continue
    EXCLUDES+=(-x "$line")
done < "$IGNORE_FILE"

echo "Creating $OUT ..."
zip -r "$OUT" . "${EXCLUDES[@]}" -x ".git/*"

echo ""
echo "Done: $OUT ($(du -h "$OUT" | cut -f1))"
echo ""
echo "Verify with: unzip -l $OUT | tail -20"
