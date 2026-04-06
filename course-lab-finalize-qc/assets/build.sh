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

xelatex -interaction=nonstopmode -halt-on-error -file-line-error -shell-escape ./main.tex

if [[ -f main.bcf ]]; then
  biber main
  xelatex -interaction=nonstopmode -halt-on-error -file-line-error -shell-escape ./main.tex
  xelatex -interaction=nonstopmode -halt-on-error -file-line-error -shell-escape ./main.tex
fi

python3 - <<'PY'
from pathlib import Path
from pypdf import PdfReader, PdfWriter

pdf_path = Path("main.pdf")
tmp_path = Path("main.normalized.pdf")

reader = PdfReader(str(pdf_path))
writer = PdfWriter()
writer.clone_document_from_reader(reader)

with tmp_path.open("wb") as handle:
    writer.write(handle)

tmp_path.replace(pdf_path)
PY

if [[ -f "$OUTDIR/main.pdf" ]]; then
  echo "OK: $OUTDIR/main.pdf"
else
  echo "Build failed: main.pdf not found"
  exit 1
fi
