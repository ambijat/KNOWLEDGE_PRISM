#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-$PWD/KNOWLEDGE_PRISM}"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$TARGET"
rsync -av --exclude '.git' "$SOURCE_DIR/" "$TARGET/"
cd "$TARGET"
python3 scripts/00_validate_project.py
python3 scripts/03_report_status.py

echo
echo "KNOWLEDGE_PRISM deployed to: $TARGET"
echo "Open this folder in VS Code when ready."
