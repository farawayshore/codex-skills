#!/usr/bin/env bash
set -euo pipefail

OUTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${REPORT_REPO_ROOT:-$(cd "$OUTDIR/../../.." && pwd)}"

if [[ ! -f "$OUTDIR/main.tex" ]]; then
  echo "Missing: $OUTDIR/main.tex"
  exit 2
fi

cd "$OUTDIR"
export TEXINPUTS="$ROOT_DIR:$ROOT_DIR/tau-class:"

pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -shell-escape ./main.tex

if [[ -f main.bcf ]]; then
  biber main
  pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -shell-escape ./main.tex
  pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -shell-escape ./main.tex
fi

if [[ -f "$OUTDIR/main.pdf" ]]; then
  echo "OK: $OUTDIR/main.pdf"
else
  echo "Build failed: main.pdf not found"
  exit 1
fi
