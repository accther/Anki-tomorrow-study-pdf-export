#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$ROOT_DIR/dist"
STAGE_DIR="$DIST_DIR/tomorrow_pdf_export"
OUTPUT_FILE="$DIST_DIR/tomorrow_pdf_export.ankiaddon"

rm -rf "$STAGE_DIR" "$OUTPUT_FILE"
mkdir -p "$STAGE_DIR"

cp "$ROOT_DIR/__init__.py" "$STAGE_DIR/"
cp "$ROOT_DIR/scheduler_snapshot.py" "$STAGE_DIR/"
cp "$ROOT_DIR/pdf_renderer.py" "$STAGE_DIR/"
cp "$ROOT_DIR/README.md" "$STAGE_DIR/"
cp "$ROOT_DIR/说明文档.zh-CN.md" "$STAGE_DIR/"
cp "$ROOT_DIR/manifest.json" "$STAGE_DIR/"

find "$STAGE_DIR" -name '__pycache__' -type d -prune -exec rm -rf {} +

(
  cd "$STAGE_DIR"
  zip -r "$OUTPUT_FILE" ./*
)

rm -rf "$STAGE_DIR"

echo "Created: $OUTPUT_FILE"
